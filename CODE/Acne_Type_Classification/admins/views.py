from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from users.forms import UserRegistrationForm
from users.models import UserRegistrationModel


# =========================
# EMAIL HELPER
# =========================

def send_user_approved_email(user):
    """Emails the user after admin approves their account."""
    login_url = f"{settings.SITE_URL}/user-login/"

    subject = "✅ Your Account Has Been Approved!"
    body = f"""Hello {user.name},

Your account has been reviewed and approved by the admin.

You can now log in using the link below:
{login_url}

Use your registered Login ID and password to access the system.

Welcome aboard!

Regards,
System"""

    send_mail(
        subject, body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )


# =========================
# ADMIN AUTH
# =========================

def AdminLogin(request):
    if request.method == 'POST':
        username = request.POST['login_id']
        pswd     = request.POST['password']
        try:
            from admins.models import AdminModel
            if AdminModel.objects.count() == 0 and username == 'admin' and pswd == 'admin':
                AdminModel.objects.create(username='admin', password='admin')

            check = AdminModel.objects.get(username=username, password=pswd)
            request.session['role'] = 'admin'
            messages.success(request, 'Welcome Admin! System access granted.')
            return redirect('AdminHome')

        except AdminModel.DoesNotExist:
            messages.error(request, 'Invalid Admin Credentials')
            return redirect('UserLogin')

    return render(request, 'AdminLogin.html')


def AdminHome(request):
    return render(request, 'admins/AdminHome.html', {})


# =========================
# USER MANAGEMENT
# =========================

def RegisterUsersView(request):
    data = UserRegistrationModel.objects.all()
    return render(request, 'admins/viewregisterusers.html', {'data': data})


def ActivaUsers(request):
    """
    Admin clicks Activate from dashboard table.
    Updates status to activated + sends approval email to user.
    """
    if request.method == 'GET':
        uid  = request.GET.get('uid')
        user = UserRegistrationModel.objects.get(id=uid)

        user.status = 'activated'
        user.save()

        try:
            send_user_approved_email(user)
            messages.success(request, f'User {user.name} activated and notified via email.')
        except Exception as e:
            print("Email error:", e)
            messages.success(request, f'User {user.name} activated. (Email notification failed)')

        return redirect('RegisterUsersView')


def send_user_deactivated_email(user):
    """Emails the user when admin deactivates their account."""
    subject = "⚠️ Your Account Has Been Deactivated"
    body = f"""Hello {user.name},

Your account has been deactivated by the admin.

If you think this was a mistake or want to know more,
please contact the admin at {settings.ADMIN_EMAIL}.

Regards,
System"""

    send_mail(
        subject, body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )


def DeactivateUsers(request):
    if request.method == 'GET':
        uid  = request.GET.get('uid')
        user = UserRegistrationModel.objects.get(id=uid)

        user.status = 'deactivated'
        user.save()

        try:
            send_user_deactivated_email(user)
            messages.success(request, f'User {user.name} deactivated and notified via email.')
        except Exception as e:
            print("Email error:", e)
            messages.success(request, f'User {user.name} deactivated. (Email notification failed)')

        return redirect('RegisterUsersView')


def DeleteUsers(request):
    if request.method == 'GET':
        uid = request.GET.get('uid')
        UserRegistrationModel.objects.filter(id=uid).delete()
        messages.success(request, 'User Deleted Successfully')
        return redirect('RegisterUsersView')


def EditUser(request):
    uid      = request.GET.get('uid')
    user_obj = UserRegistrationModel.objects.get(id=uid)

    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('password'):
            post_data['password'] = user_obj.password

        form = UserRegistrationForm(post_data, instance=user_obj)
        form.fields['loginid'].widget.attrs['readonly']    = True
        form.fields['last_login'].widget.attrs['readonly'] = True

        if form.is_valid():
            form.save()
            messages.success(request, f'Details for {user_obj.name} updated successfully.')
            return redirect('RegisterUsersView')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm(instance=user_obj)
        form.fields['loginid'].widget.attrs['readonly']    = True
        form.fields['last_login'].widget.attrs['readonly'] = True
        form.fields['password'].widget.render_value        = True
        form.fields['password'].required                   = False
        form.fields['password'].help_text                  = "Leave blank to keep the current password."

    return render(request, 'admins/edit_user.html', {'form': form, 'user': user_obj})


# =========================
# EMAIL APPROVE LINK HANDLER
# =========================

def ApproveUserViaEmail(request, token):
    """
    Admin clicks approve link directly from their email.
    Token acts as the security key — no login needed.
    """
    user = get_object_or_404(UserRegistrationModel, approve_token=token)

    if user.status == 'activated':
        return render(request, 'admins/already_approved.html', {'user': user})

    user.status = 'activated'
    user.save()

    try:
        send_user_approved_email(user)
    except Exception as e:
        print("Approval email error:", e)

    return render(request, 'admins/approved_success.html', {'user': user})