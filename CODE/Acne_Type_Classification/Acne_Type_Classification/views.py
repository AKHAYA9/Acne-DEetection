from django.shortcuts import render, redirect
from django.contrib import messages
from users.forms import UserRegistrationForm
from users.models import UserRegistrationModel
from django.utils import timezone

def index(request):
    return render(request, 'index.html', {})

def UserLogin(request):
    if request.method == "POST":
        role = request.POST.get('role')
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')

        if role == 'admin':
            try:
                from admins.models import AdminModel
                if AdminModel.objects.count() == 0 and loginid == 'admin' and pswd == 'admin':
                    # Fallback for initial setup if table is empty
                    AdminModel.objects.create(username='admin', password='admin')
                
                check = AdminModel.objects.get(username=loginid, password=pswd)
                request.session['role'] = 'admin'
                return redirect('AdminHome')
            except AdminModel.DoesNotExist:
                messages.error(request, 'Invalid Admin Credentials')
                return render(request, 'UserLogin.html')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return render(request, 'UserLogin.html')
        
        elif role == 'user':
            try:
                check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
                if check.status == "activated":
                    check.last_login = timezone.now()
                    check.save()
                    
                    request.session['id'] = check.id
                    request.session['loggeduser'] = check.name
                    request.session['loginid'] = loginid
                    request.session['email'] = check.email
                    request.session['role'] = 'user'
                    return redirect('UserHome')
                else:
                    messages.error(request, 'Your Account is not activated or is deactivated.')
                    return render(request, 'UserLogin.html')
            except UserRegistrationModel.DoesNotExist:
                messages.error(request, 'Invalid Login ID or Password')
                return render(request, 'UserLogin.html')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return render(request, 'UserLogin.html')

    return render(request, 'UserLogin.html', {})


def UserRegister(request):
    form = UserRegistrationForm()
    return render(request, 'UserRegistrations.html', {'form': form})