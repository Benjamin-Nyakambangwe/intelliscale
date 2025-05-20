from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden # For access denied
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserUpdateForm



# --- Role Check Decorators ---
def is_admin(user):
    return user.is_authenticated and user.role == 'admin' or user.is_superuser

def is_manager(user):
    return user.is_authenticated and user.role == 'manager'

def is_operator(user):
    return user.is_authenticated and user.role == 'operator'

# --- Custom Login View for Redirection ---
class CustomLoginView(LoginView):
    template_name = 'login.html' 

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'admin' or user.is_superuser: 
                return reverse_lazy('scale:admin_dashboard')
            elif user.role == 'manager':
                return reverse_lazy('scale:manager_dashboard')
            elif user.role == 'operator':
                return reverse_lazy('scale:operator_dashboard')
        return reverse_lazy('scale:default_dashboard') # Fallback

# --- Dashboard Views (Protected) ---
@login_required
# @user_passes_test(is_admin, login_url=reverse_lazy('accounts:login')) # More robust check
def admin_dashboard(request):
    # Simple check (decorator is better for reusability)
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return HttpResponseForbidden("You don't have permission to access this page.") # Or redirect
    return render(request, 'scale/admin_dashboard.html')

@login_required
# @user_passes_test(is_manager, login_url=reverse_lazy('accounts:login'))
def manager_dashboard(request):
    if not request.user.role == 'manager':
        return HttpResponseForbidden("You don't have permission to access this page.")
    return render(request, 'scale/manager_dashboard.html')

@login_required
# @user_passes_test(is_operator, login_url=reverse_lazy('accounts:login'))
def operator_dashboard(request):
    if not request.user.role == 'operator':
        return HttpResponseForbidden("You don't have permission to access this page.")
    return render(request, 'scale/operator_dashboard.html')

@login_required
def default_dashboard(request):
    return render(request, 'scale/default_dashboard.html', {'username': request.user.username})


# --- User Management Views ---
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin role for views"""
    
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('scale:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = CustomUser.objects.all().order_by('username')
    return render(request, 'users/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'users/user_detail.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} was created successfully.')
            return redirect('users:user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/user_create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} was updated successfully.')
            return redirect('users:user_detail', pk=user.pk)
    else:
        form = CustomUserUpdateForm(instance=user)
    
    return render(request, 'users/user_edit.html', {'form': form, 'user': user})

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} was deleted successfully.')
        return redirect('users:user_list')
    
    # If not POST, redirect to detail page
    return redirect('users:user_detail', pk=pk)