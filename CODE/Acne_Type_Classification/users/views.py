from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from users.models import UserRegistrationModel, AcnePredictionModel
from users.forms import UserRegistrationForm


# =========================
# EMAIL HELPER
# =========================

def send_admin_notification(user):
    approve_url = f"{settings.SITE_URL}/approve-user/{user.approve_token}/"

    subject = f"[Action Required] New User Registered: {user.name}"
    body = f"""Hello Admin,

A new user has registered and is waiting for your approval.

Name   : {user.name}
Email  : {user.email}
Mobile : {user.mobile}

Click the link below to approve this user instantly:
{approve_url}

If you do not recognise this user, simply ignore this email.

Regards,
System"""

    send_mail(
        subject, body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        fail_silently=False
    )

import random
from users.models import UserRegistrationModel, PasswordResetOTP


def ForgotPassword(request):
    """Step 1 — User enters their registered email."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = UserRegistrationModel.objects.get(email=email)

            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))

            # Save OTP to DB (invalidate old ones first)
            PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
            PasswordResetOTP.objects.create(user=user, otp=otp)

            # Send OTP email
            send_mail(
                'Your Password Reset OTP',
                f"""Hello {user.name},

Your OTP for password reset is:

        {otp}

This OTP is valid for 10 minutes. Do not share it with anyone.

If you did not request this, ignore this email.

Regards,
System""",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False
            )

            # Store email in session to use in next steps
            request.session['reset_email'] = email
            messages.success(request, f'OTP sent to {email}. Check your inbox.')
            return redirect('VerifyOTP')

        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'No account found with this email.')

    return render(request, 'ForgotPassword.html')


def VerifyOTP(request):
    """Step 2 — User enters the OTP received in email."""
    if 'reset_email' not in request.session:
        return redirect('ForgotPassword')

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        email       = request.session.get('reset_email')

        try:
            user = UserRegistrationModel.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(
                user=user, otp=otp_entered, is_used=False
            ).latest('created_at')

            if otp_record.is_expired():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('ForgotPassword')

            # Mark OTP as used
            otp_record.is_used = True
            otp_record.save()

            # Allow access to reset password page
            request.session['otp_verified'] = True
            return redirect('ResetPassword')

        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'VerifyOTP.html')


def ResetPassword(request):
    """Step 3 — User sets a new password."""
    if 'reset_email' not in request.session or not request.session.get('otp_verified'):
        return redirect('ForgotPassword')

    if request.method == 'POST':
        new_password     = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'ResetPassword.html')

        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'ResetPassword.html')

        email = request.session.get('reset_email')
        UserRegistrationModel.objects.filter(email=email).update(password=new_password)

        # Clear session keys used for reset flow
        del request.session['reset_email']
        del request.session['otp_verified']

        messages.success(request, 'Password reset successful! You can now log in.')
        return redirect('UserLogin')

    return render(request, 'ResetPassword.html')
    
# =========================
# USER PAGES
# =========================

def UserHome(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    return render(request, 'users/UserHomePage.html', {})


def UserRegisterActions(request):               # ← this is what your form posts to
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.status = 'pending'             # always starts as pending
            user.save()

            try:
                send_admin_notification(user)   # 📧 email admin
                messages.success(request, 'Registration successful! Please wait for admin approval. Admin will notify you via email.')
            except Exception as e:
                print("Admin email error:", e)
                messages.success(request, 'Registration successful! Please wait for admin approval.')

            return redirect('UserLogin')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UserRegistrationForm()

    return render(request, 'UserRegistrations.html', {'form': form})


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def history(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    user = UserRegistrationModel.objects.get(id=request.session['id'])
    records_list = AcnePredictionModel.objects.filter(user=user).order_by('-id')
    
    paginator = Paginator(records_list, 10) # 10 records per page
    page = request.GET.get('page')
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)
        
    return render(request, 'users/history.html', {'records': records})


def DeletePrediction(request, id):
    if 'id' not in request.session:
        return redirect('UserLogin')
    user = UserRegistrationModel.objects.get(id=request.session['id'])
    try:
        record = AcnePredictionModel.objects.get(id=id, user=user)
        record.delete()
        messages.success(request, 'Record deleted successfully.')
    except AcnePredictionModel.DoesNotExist:
        messages.error(request, 'Record not found.')
    return redirect('UserHistory')


def DeleteSelectedPredictions(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    if request.method == 'POST':
        user = UserRegistrationModel.objects.get(id=request.session['id'])
        record_ids = request.POST.getlist('selected_ids')
        action = request.POST.get('action')
        
        if action == 'delete_all':
            deleted_count, _ = AcnePredictionModel.objects.filter(user=user).delete()
            if deleted_count > 0:
                messages.success(request, f'All {deleted_count} records deleted successfully.')
            else:
                messages.warning(request, 'No records to delete.')
        elif record_ids:
            deleted_count, _ = AcnePredictionModel.objects.filter(id__in=record_ids, user=user).delete()
            if deleted_count > 0:
                messages.success(request, f'Selected {deleted_count} record(s) deleted successfully.')
            else:
                messages.warning(request, 'No records found to delete.')
        else:
            messages.warning(request, 'No records selected.')
            
    return redirect('UserHistory')


import base64
import requests
import json
import time
from django.core.files.base import ContentFile
from django.http import JsonResponse

import os
import tempfile

# Hugging Face Settings
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
HF_SPACE_ID = "Akhya/acne-yolo-api"


def query_huggingface_api(image_bytes):
    from gradio_client import Client, handle_file

    # Write image bytes to a temporary file because gradio_client requires a local file path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    try:
        temp_file.write(image_bytes)
        temp_file.close()
        
        # Initialize Gradio Space Client
        client = Client(HF_SPACE_ID, token=HF_API_TOKEN if HF_API_TOKEN else None)
        result = client.predict(

            image=handle_file(temp_file.name),
            api_name="/predict"
        )
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
        except Exception:
            pass

def parse_prediction(response_json):
    if isinstance(response_json, list):
        if len(response_json) == 0:
            return "No Acne Detected"
            
        # Try reading class and confidence first (YOLO)
        first_item = response_json[0]
        if isinstance(first_item, dict):
            if 'class' in first_item:
                # Sort detections by confidence descending
                sorted_results = sorted(response_json, key=lambda x: x.get('confidence', 0), reverse=True)
                top_result = sorted_results[0].get('class', 'Unknown')
                return top_result.replace('_', ' ').title()
            elif 'label' in first_item:
                # Standard classification model fallback
                sorted_results = sorted(response_json, key=lambda x: x.get('score', 0), reverse=True)
                top_result = sorted_results[0].get('label', 'Unknown')
                return top_result.replace('_', ' ').title()
                
    elif isinstance(response_json, dict):
        if 'error' in response_json:
            return f"Error: {response_json.get('error')}"
        elif 'label' in response_json:
            return response_json.get('label').replace('_', ' ').title()
        elif 'class' in response_json:
            return response_json.get('class').replace('_', ' ').title()
            
    return "Unknown Skin State"

def get_severity_info(result_label):
    lbl = result_label.lower()
    if "no acne" in lbl:
        return {
            "severity": "None",
            "icon": "fa-check-circle",
            "description": "No acne lesions or spots were detected on the scanned skin area.",
            "cure": "Continue with your regular skin care routine and maintain proper hygiene.",
            "precautions": "Protect your skin from excessive sun exposure and keep it clean."
        }
    elif any(k in lbl for k in ["cyst", "nodule", "severe", "level 3"]):
        return {
            "severity": "Severe",
            "icon": "fa-exclamation-triangle",
            "description": "Deep, painful, pus-filled acne lesions that can cause permanent scarring.",
            "cure": "Requires clinical dermatologist attention. Treatments often include oral isotretinoin or prescription-strength topical applications.",
            "precautions": "Avoid popping, squeezing, or picking the area. Consult a certified medical professional."
        }
    elif any(k in lbl for k in ["papule", "pustule", "moderate", "level 2"]):
        return {
            "severity": "Moderate",
            "icon": "fa-exclamation-circle",
            "description": "Inflamed red bumps on the skin, often filled with yellow or white pus heads.",
            "cure": "Benzoyl peroxide washes, topical retinoids, or spot treatments recommended by a dermatologist.",
            "precautions": "Cleanse gently twice a day. Avoid scrubbing with rough washcloths or brushes."
        }
    else:
        return {
            "severity": "Mild",
            "icon": "fa-check-circle",
            "description": "Non-inflammatory clogged pores, commonly appearing as open (black) or closed (white) comedones.",
            "cure": "Over-the-counter salicylic acid or glycolic acid cleansers and gentle non-comedogenic moisturizers.",
            "precautions": "Use oil-free makeup and skincare products. Keep the face clean and sweat-free."
        }


def get_detailed_acne_info(result_label):
    lbl = result_label.lower()
    
    # 1. CYSTS
    if "cyst" in lbl or "nodule" in lbl:
        return {
            "name": "Cysts / Nodules",
            "severity": "Severe",
            "badge_class": "badge-danger",
            "icon": "fa-exclamation-triangle",
            "desc": "Large, painful acne lesions deep under the skin that can cause permanent scarring.",
            "regions": [
                {
                    "region": "Forehead",
                    "why": "Excessive oil production, stress, sweat buildup, and hair care products (pomades/sprays) blocking pores.",
                    "prevention": "Use non-comedogenic hair products; wash your forehead after sweating.",
                    "remedy": "Dermatologist consultation for oral or topical prescription treatments."
                },
                {
                    "region": "Cheeks",
                    "why": "Dirty pillowcases, direct phone contact, bacterial buildup, or friction.",
                    "prevention": "Disinfect phone screen daily, change pillowcases every 2-3 days, avoid touching face.",
                    "remedy": "Gentle salicylic acid washes; avoid picking or squeezing lesions."
                },
                {
                    "region": "Chin & Jawline",
                    "why": "Strong hormonal influence, androgen hormone activity, and stress-induced fluctuations.",
                    "prevention": "Manage stress levels; maintain consistent sleep cycles; check hormonal balance.",
                    "remedy": "Clinical treatments prescribed by a dermatologist."
                },
                {
                    "region": "Nose",
                    "why": "Extremely oily T-zone with large pores that collect excess sebum and dead skin.",
                    "prevention": "Use oil-control cleansers; exfoliate regularly with mild chemical exfoliants (BHAs).",
                    "remedy": "Dermatologist-recommended topical retinoids or spot applications."
                }
            ]
        }
    
    # 2. PUSTULES
    elif "pustule" in lbl:
        return {
            "name": "Pustules",
            "severity": "Moderate",
            "badge_class": "badge-warning",
            "icon": "fa-exclamation-circle",
            "desc": "Red, inflamed skin bumps filled with pus near the surface.",
            "regions": [
                {
                    "region": "Forehead",
                    "why": "Excessive oil production, stress, sweat buildup, and hair care products (pomades/sprays) blocking pores.",
                    "prevention": "Wash face immediately after workouts; keep hair off forehead.",
                    "remedy": "Benzoyl peroxide wash or spot treatment to kill bacteria."
                },
                {
                    "region": "Cheeks",
                    "why": "Bacterial transfer from dirty hands, makeup brushes, or heavy cosmetic products.",
                    "prevention": "Clean makeup brushes weekly; use oil-free (non-comedogenic) makeup.",
                    "remedy": "Salicylic acid cleansers and lightweight, oil-free moisturizers."
                },
                {
                    "region": "Chin",
                    "why": "Hormonal flares and friction from touching or resting the chin on hands.",
                    "prevention": "Avoid resting your face on your hands; keep hands clean.",
                    "remedy": "Apply thin layer of benzoyl peroxide or prescription topical retinoids."
                },
                {
                    "region": "Nose",
                    "why": "Oily pores that become infected with Propionibacterium acnes.",
                    "prevention": "Double cleanse at night if wearing sunscreen or makeup; use pore-clearing BHA.",
                    "remedy": "Clay masks to absorb oil; spot treatment with tea tree oil or benzoyl peroxide."
                }
            ]
        }
        
    # 3. PAPULES
    elif "papule" in lbl:
        return {
            "name": "Papules",
            "severity": "Mild to Moderate",
            "badge_class": "badge-warning",
            "icon": "fa-exclamation-circle",
            "desc": "Small, red, solid inflamed bumps on the skin surface that do not contain pus.",
            "regions": [
                {
                    "region": "Forehead",
                    "why": "Excessive oil production, stress, sweat buildup, and hair care products (pomades/sprays) blocking pores.",
                    "prevention": "Ensure gentle daily exfoliation; avoid harsh face scrubs.",
                    "remedy": "Salicylic acid cleansers to keep pores clear."
                },
                {
                    "region": "Cheeks",
                    "why": "Skin irritation, friction (e.g., from masks or pillowcases), and environmental dirt.",
                    "prevention": "Wash face after coming home from polluted areas; use clean masks.",
                    "remedy": "Soothe with centella asiatica, niacinamide, or aloe vera."
                },
                {
                    "region": "Jawline",
                    "why": "Hormonal triggers causing sebum glands to swell.",
                    "prevention": "Avoid tight collars or chinstraps; maintain a healthy anti-inflammatory diet.",
                    "remedy": "Topical retinoids at night to promote cell turnover."
                },
                {
                    "region": "Nose",
                    "why": "Oil accumulation inside large pores that becomes irritated.",
                    "prevention": "Use a gentle clay mask once a week; keep T-zone hydrated with light gels.",
                    "remedy": "Salicylic acid or glycolic acid spot applications."
                }
            ]
        }
        
    # 4. WHITEHEADS
    elif "whitehead" in lbl:
        return {
            "name": "Whiteheads",
            "severity": "Mild",
            "badge_class": "badge-success",
            "icon": "fa-check-circle",
            "desc": "Closed clogged pores where oil and dead skin cells are trapped underneath the surface.",
            "regions": [
                {
                    "region": "Forehead",
                    "why": "Excessive oil production, stress, sweat buildup, and hair care products (pomades/sprays) blocking pores.",
                    "prevention": "Exfoliate weekly with chemical exfoliants; keep skin hydrated.",
                    "remedy": "Alpha hydroxy acids (AHA) or salicylic acid (BHA)."
                },
                {
                    "region": "Nose",
                    "why": "Large sebaceous glands producing oil that gets trapped by tight pores.",
                    "prevention": "Keep the area clean; avoid picking or squeezing.",
                    "remedy": "Salicylic acid or gentle retinoids."
                },
                {
                    "region": "Chin",
                    "why": "Hormonal changes.",
                    "prevention": "Ensure double-cleansing in the evening.",
                    "remedy": "Retinol or adapalene to regulate skin cells."
                },
                {
                    "region": "Cheeks",
                    "why": "Cosmetic or skincare products containing pore-clogging ingredients.",
                    "prevention": "Verify that all skincare/makeup labels read 'non-comedogenic'.",
                    "remedy": "Stop using heavy oils or creams; switch to gel-based formulas."
                }
            ]
        }
        
    # 5. BLACKHEADS
    elif "blackhead" in lbl:
        return {
            "name": "Blackheads",
            "severity": "Mild",
            "badge_class": "badge-success",
            "icon": "fa-check-circle",
            "desc": "Open clogged pores where sebum and dead skin cells oxidize upon contact with air, turning black.",
            "regions": [
                {
                    "region": "Nose",
                    "why": "Highly concentrated sebaceous glands and larger pores that easily oxidize.",
                    "prevention": "Avoid pore strips; use BHA.",
                    "remedy": "Regular application of Salicylic Acid (BHA) to dissolve oil inside pores."
                },
                {
                    "region": "Forehead",
                    "why": "Excessive oil production, stress, sweat buildup, and hair care products (pomades/sprays) blocking pores.",
                    "prevention": "Wash face twice daily with a gentle foaming cleanser.",
                    "remedy": "Clay masks to draw out impurities; niacinamide to regulate oil."
                },
                {
                    "region": "Chin",
                    "why": "Hormonal oil production pooling in the creases of the chin.",
                    "prevention": "Ensure the chin area is thoroughly cleansed.",
                    "remedy": "Retinol to help keep the skin surface clear and prevent oxidation."
                },
                {
                    "region": "Cheeks",
                    "why": "Dirt, pollution, and oil accumulating over time.",
                    "prevention": "Keep makeup light and use clean towels.",
                    "remedy": "Oil cleansing followed by a gentle gel cleanser."
                }
            ]
        }
        
    # Default
    else:
        return {
            "name": "Healthy Skin",
            "severity": "None",
            "badge_class": "badge-success",
            "icon": "fa-smile",
            "desc": "No acne lesions detected. Keep up the good work maintaining healthy skin!",
            "regions": [
                {
                    "region": "All Face Regions",
                    "why": "Well-balanced sebum production and clear pores.",
                    "prevention": "Protect your skin barrier; apply broad-spectrum sunscreen daily; stay hydrated.",
                    "remedy": "Maintain your current clean skincare routine."
                }
            ]
        }


def knowledge_base(request):
    cysts = get_detailed_acne_info("cyst")
    pustules = get_detailed_acne_info("pustule")
    papules = get_detailed_acne_info("papule")
    whiteheads = get_detailed_acne_info("whitehead")
    blackheads = get_detailed_acne_info("blackhead")
    
    context = {
        'cysts': cysts,
        'pustules': pustules,
        'papules': papules,
        'whiteheads': whiteheads,
        'blackheads': blackheads
    }
    return render(request, 'knowledge_base.html', context)


REGIONAL_DETAILS = {
    "forehead": {
        "region": "Forehead",
        "why": "Excessive oil production (sebum) from overactive sebaceous glands, high stress levels triggering cortisol release, sweat buildup (especially during workouts), friction from hats/helmets, and hair care products (heavy pomades, waxes, or sprays containing silicones/oils) blocking pores along the hairline.",
        "prevention": "Exfoliate weekly with gentle chemical exfoliants, keep the forehead area clean, wash immediately after sweating, and use non-comedogenic hair care products.",
        "remedy": "Cleanse daily using a salicylic acid (2% BHA) wash to clear pores, apply a lightweight oil-free gel moisturizer, and consider using topical retinoids at night.",
        "diet": "Avoid high-glycemic foods, processed sugars, and excessive dairy. Focus on drinking 2-3 liters of water daily, drinking green tea, and eating antioxidant-rich berries and green leafy vegetables."
    },
    "cheeks": {
        "region": "Cheeks",
        "why": "Bacterial transfer from dirty mobile phone screens, infrequent washing of pillowcases, dirty makeup brushes, touching the face with unclean hands, and the use of heavy comedogenic makeup, thick creams, or environmental pollution blocking pores.",
        "prevention": "Sanitize your phone screen daily, change pillowcases every 2-3 days, wash makeup brushes weekly, and avoid touching your cheeks.",
        "remedy": "Use gentle cleansers with salicylic acid, switch to oil-free/non-comedogenic cosmetics, and use soothing ingredients like niacinamide or centella asiatica.",
        "diet": "Reduce intake of inflammatory trans-fats and processed dairy. Increase consumption of Omega-3 fatty acids (flaxseeds, walnuts, fish) and probiotics (yogurt, kefir) to reduce systemic skin inflammation."
    },
    "nose": {
        "region": "Nose",
        "why": "Higher concentration of large sebaceous glands in the T-zone producing excess sebum, accumulation of dead skin cells blocking pores, and manual nose-picking introducing bacteria into oxidized open comedones (blackheads).",
        "prevention": "Keep the area clean, double cleanse in the evening to remove sunscreen/makeup, and avoid manually squeezing blackheads.",
        "remedy": "Incorporate beta hydroxy acids (salicylic acid) to dissolve oil, use clay masks (kaolin/bentonite) weekly, and apply gentle topical retinoids to regulate pore lining.",
        "diet": "Limit spicy foods, high-sodium foods, and saturated fats to minimize vascular dilation and oil gland activity. Eat zinc-rich foods (pumpkin seeds) and vitamin A-rich foods (carrots, sweet potatoes)."
    },
    "chin": {
        "region": "Chin",
        "why": "Strongly linked to hormonal fluctuations (particularly androgens stimulating sebum glands) during menstrual cycles, stress, or conditions like PCOS, as well as friction from resting the chin on dirty hands.",
        "prevention": "Ensure thorough cleansing, avoid resting your chin on your hands, and maintain consistent sleep patterns.",
        "remedy": "Apply thin layers of benzoyl peroxide or prescription topical retinoids, and consult a dermatologist for hormonal treatments if chronic.",
        "diet": "Reduce dairy intake and high-glycemic foods. Consume hormone-balancing cruciferous vegetables (broccoli, cabbage), spearmint tea (known to have anti-androgenic properties), and healthy fats (avocado)."
    },
    "jawline": {
        "region": "Jawline",
        "why": "Hormonal triggers causing sebum glands to swell, friction from tight collars or chinstraps, and systemic inflammation pooling in the lower face area.",
        "prevention": "Avoid tight clothing or straps near the jaw, maintain a consistent nighttime skincare routine, and minimize stress.",
        "remedy": "Use topical retinoids (adapalene/retinol) at night to boost cell turnover, and use gentle, non-stripping cleansers.",
        "diet": "Limit dairy and refined sugars. Incorporate anti-inflammatory foods, leafy greens, green tea, and omega-3 supplements to soothe hormonal flares."
    }
}

def get_region_diagnostics(region_name):
    if not region_name:
        return None
    r = region_name.lower().strip()
    if "chin" in r and "jawline" in r:
        return REGIONAL_DETAILS["chin"]
    elif "chin" in r:
        return REGIONAL_DETAILS["chin"]
    elif "jawline" in r:
        return REGIONAL_DETAILS["jawline"]
    elif "forehead" in r:
        return REGIONAL_DETAILS["forehead"]
    elif "cheek" in r:
        return REGIONAL_DETAILS["cheeks"]
    elif "nose" in r:
        return REGIONAL_DETAILS["nose"]
    return None


def upload_image_prediction(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
        
    if request.method == 'POST':
        image_file = request.FILES.get('image')
        if not image_file:
            messages.error(request, "Please select an image file to upload.")
            return render(request, 'users/upload.html')
            
        try:
            # Read image bytes to send to Hugging Face
            image_bytes = image_file.read()
            image_file.seek(0) # Reset pointer
            
            # Query Hugging Face
            api_res = query_huggingface_api(image_bytes)
            if isinstance(api_res, dict) and "error" in api_res:
                raise Exception(api_res["error"])
                
            result_label = parse_prediction(api_res)
            region = request.POST.get('region')
            
            # Save record
            user = UserRegistrationModel.objects.get(id=request.session['id'])
            record = AcnePredictionModel(
                user=user,
                image=image_file,
                result=result_label[:100],  # Ensure length safety
                region=region,
                model_name=f"HuggingFace/{HF_SPACE_ID}"
            )
            
            # Draw boxes if coordinates are present in the response
            if isinstance(api_res, list):
                from PIL import Image, ImageDraw
                import io
                from django.core.files.base import ContentFile
                try:
                    img = Image.open(io.BytesIO(image_bytes))
                    draw = ImageDraw.Draw(img)
                    has_boxes = False
                    for det in api_res:
                        box = det.get('box')
                        if box and len(box) == 4:
                            has_boxes = True
                            draw.rectangle(box, outline="#00f2fe", width=3)
                            # Draw label background and text
                            label_txt = f"{det.get('class', 'Acne')} {int(det.get('confidence', 0)*100)}%"
                            draw.rectangle([box[0], max(0, box[1] - 15), box[0] + 120, box[1]], fill="#00f2fe")
                            draw.text((box[0] + 2, max(0, box[1] - 15)), label_txt, fill="#0f172a")
                    if has_boxes:
                        out_io = io.BytesIO()
                        img.save(out_io, format="JPEG")
                        record.annotated_image.save(f"annotated_{int(time.time())}.jpg", ContentFile(out_io.getvalue()), save=False)
                except Exception as draw_err:
                    print(f"Error drawing boxes: {draw_err}")
            
            record.save()
            info = get_severity_info(result_label)
            detailed_info = get_detailed_acne_info(result_label)
            
            selected_region_info = get_region_diagnostics(region)
            
            return render(request, 'users/upload.html', {
                'result': result_label,
                'prediction': record,
                'info': info,
                'detailed_info': detailed_info,
                'selected_region': region,
                'selected_region_info': selected_region_info
            })
        except Exception as e:
            messages.error(request, f"Inference engine failure: {str(e)}")
            return render(request, 'users/upload.html')
            
    return render(request, 'users/upload.html')


def live_prediction(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    return render(request, 'users/live_prediction.html')


def capture_prediction(request):
    if 'id' not in request.session:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'})
        
    if request.method == 'POST':
        try:
            body_data = json.loads(request.body)
            img_data_url = body_data.get('image')
            region = body_data.get('region')
            if not img_data_url:
                return JsonResponse({'status': 'error', 'message': 'No image data sent'})
                
            # Decode base64 image data
            format_str, img_str = img_data_url.split(';base64,')
            ext = format_str.split('/')[-1]
            image_data = base64.b64decode(img_str)
            
            # Save to ContentFile
            filename = f"capture_{int(time.time())}.{ext}"
            content_file = ContentFile(image_data, name=filename)
            
            # Query Hugging Face API
            api_res = query_huggingface_api(image_data)
            if isinstance(api_res, dict) and "error" in api_res:
                raise Exception(api_res["error"])
                
            result_label = parse_prediction(api_res)
            
            # Save record to DB
            user = UserRegistrationModel.objects.get(id=request.session['id'])
            record = AcnePredictionModel(
                user=user,
                image=content_file,
                result=result_label[:100],  # Ensure length safety
                region=region,
                model_name=f"HuggingFace/{HF_SPACE_ID}"
            )
            
            # Draw boxes if coordinates are present in the response
            if isinstance(api_res, list):
                from PIL import Image, ImageDraw
                import io
                try:
                    img = Image.open(io.BytesIO(image_data))
                    draw = ImageDraw.Draw(img)
                    has_boxes = False
                    for det in api_res:
                        box = det.get('box')
                        if box and len(box) == 4:
                            has_boxes = True
                            draw.rectangle(box, outline="#00f2fe", width=3)
                            # Draw label background and text
                            label_txt = f"{det.get('class', 'Acne')} {int(det.get('confidence', 0)*100)}%"
                            draw.rectangle([box[0], max(0, box[1] - 15), box[0] + 120, box[1]], fill="#00f2fe")
                            draw.text((box[0] + 2, max(0, box[1] - 15)), label_txt, fill="#0f172a")
                    if has_boxes:
                        out_io = io.BytesIO()
                        img.save(out_io, format="JPEG")
                        record.annotated_image.save(f"annotated_{int(time.time())}.jpg", ContentFile(out_io.getvalue()), save=False)
                except Exception as draw_err:
                    print(f"Error drawing boxes: {draw_err}")
                    
            record.save()
            
            result_image_url = record.annotated_image.url if record.annotated_image else record.image.url
            
            detailed_info = get_detailed_acne_info(result_label)
            selected_region_info = get_region_diagnostics(region)
            
            return JsonResponse({
                'status': 'success',
                'result': result_label,
                'image': result_image_url,
                'region': region,
                'why': selected_region_info['why'] if selected_region_info else '',
                'prevention': selected_region_info['prevention'] if selected_region_info else '',
                'remedy': selected_region_info['remedy'] if selected_region_info else '',
                'diet': selected_region_info['diet'] if selected_region_info else '',
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Inference error: {str(e)}"})
            
    return JsonResponse({'status': 'error', 'message': 'POST request required'})


def UserLogout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('UserLogin')