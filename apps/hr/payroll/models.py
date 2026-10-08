from django.db import models

class SalarySetting(models.Model):
    employee = models.OneToOneField('employees.Employee', on_delete=models.CASCADE, related_name='salary_setting', verbose_name="Karyawan")
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Rate Gaji per Hari")
    allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tunjangan Bulanan")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Gaji {self.employee.full_name or self.employee.user.username}"

class Payslip(models.Model):
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='payslips')
    month = models.IntegerField(verbose_name="Bulan")
    year = models.IntegerField(verbose_name="Tahun")
    
    total_attendance = models.IntegerField(default=0, verbose_name="Total Kehadiran (Hari)")
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Rate Gaji")
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Gaji Pokok")
    allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tunjangan")
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Potongan")
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Gaji Bersih")
    
    status = models.CharField(max_length=20, choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published (Bisa dilihat karyawan)'), ('PAID', 'Sudah Dibayar')], default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('employee', 'month', 'year')
        
    def __str__(self):
        return f"Slip {self.employee.full_name or self.employee.user.username} - {self.month}/{self.year}"
        
    def calculate_salary(self):
        self.basic_salary = self.total_attendance * self.daily_rate
        self.net_salary = self.basic_salary + self.allowance - self.deduction
        self.save()
