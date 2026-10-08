from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions
from .models import Branch, Department, Position
from .serializers import BranchSerializer, DepartmentSerializer, PositionSerializer
from .forms import BranchForm
from apps.accounts.views import IsSuperAdminOrReadOnly

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by('name')
    serializer_class = BranchSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().select_related('branch').order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all().select_related('department__branch').order_by('name')
    serializer_class = PositionSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

@login_required
def branch_list(request):
    branches = Branch.objects.all()
    context = {'branches': branches}
    return render(request, 'hrga/organizations/branch_list.html', context)

@login_required
def branch_create(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cabang berhasil ditambahkan.')
            return redirect('organizations:branch_list')
    else:
        form = BranchForm()
    
    return render(request, 'hrga/organizations/branch_edit.html', {'form': form})
