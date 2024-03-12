# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm, SignUpForm


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


# In your views.py
from django.contrib.auth.models import Group
from .forms import LoginForm, SignUpForm


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # This now creates and returns the user instance
            role_name = form.cleaned_data.get('role')
            group = Group.objects.get(name=role_name)  # Retrieve the corresponding group for the role
            user.groups.add(group)  # Add the user to the group
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])

            msg = 'User created successfully.'
            success = True

            # Optionally, log the user in and redirect them to another page
            # login(request, user)
            # return redirect("/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})