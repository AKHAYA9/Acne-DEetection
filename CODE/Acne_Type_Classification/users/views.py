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


def history(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    user    = UserRegistrationModel.objects.get(id=request.session['id'])
    records = AcnePredictionModel.objects.filter(user=user).order_by('-id')
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


def upload_image_prediction(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    return render(request, 'users/upload.html')


def live_prediction(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    return render(request, 'users/live_prediction.html')


def capture_prediction(request):
    if 'id' not in request.session:
        return redirect('UserLogin')
    return render(request, 'users/upload.html')


def UserLogout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('UserLogin')