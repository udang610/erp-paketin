import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import 'package:intl/intl.dart';
import '../provider/payroll_provider.dart';

class PayrollScreen extends ConsumerWidget {
  const PayrollScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final payslipsAsync = ref.watch(payslipListProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Slip Gaji'),
      ),
      body: payslipsAsync.when(
        data: (payslips) {
          if (payslips.isEmpty) {
            return const Center(child: Text('Belum ada slip gaji tersedia.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: payslips.length,
            itemBuilder: (context, index) {
              final slip = payslips[index];
              final formatCurrency = NumberFormat.currency(locale: 'id_ID', symbol: 'Rp', decimalDigits: 0);
              final netSalary = double.tryParse(slip['net_salary'].toString()) ?? 0.0;
              final month = slip['month'];
              final year = slip['year'];
              final status = slip['status'] ?? 'DRAFT';

              return Card(
                margin: const EdgeInsets.only(bottom: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  leading: CircleAvatar(
                    backgroundColor: Colors.green[100],
                    child: const Icon(Icons.request_quote, color: Colors.green),
                  ),
                  title: Text('Gaji $month/$year', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 4),
                      Text('Total Kehadiran: ${slip['total_attendance']} hari'),
                      Text('Status: $status'),
                    ],
                  ),
                  trailing: Text(
                    formatCurrency.format(netSalary),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.blue),
                  ),
                  onTap: () {
                    // Tampilkan detail slip gaji
                    showModalBottomSheet(
                      context: context,
                      builder: (ctx) => _buildDetailBottomSheet(context, slip, formatCurrency, isDark),
                    );
                  },
                ),
              );
            },
          );
        },
        loading: () => ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: 3,
          itemBuilder: (context, index) => Shimmer.fromColors(
            baseColor: Colors.grey[300]!,
            highlightColor: Colors.grey[100]!,
            child: Container(
              height: 100,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        error: (err, _) => Center(child: Text(err.toString())),
      ),
    );
  }

  Widget _buildDetailBottomSheet(BuildContext context, Map<String, dynamic> slip, NumberFormat formatCurrency, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('Detail Slip Gaji', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const Divider(height: 32),
          _buildDetailRow('Gaji Pokok', slip['basic_salary'], formatCurrency),
          const SizedBox(height: 8),
          _buildDetailRow('Tunjangan', slip['allowance'], formatCurrency),
          const SizedBox(height: 8),
          _buildDetailRow('Potongan', slip['deduction'], formatCurrency, isDeduction: true),
          const Divider(height: 32),
          _buildDetailRow('Gaji Bersih', slip['net_salary'], formatCurrency, isTotal: true),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Tutup'),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, dynamic value, NumberFormat formatCurrency, {bool isDeduction = false, bool isTotal = false}) {
    final valDouble = double.tryParse(value.toString()) ?? 0.0;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(fontWeight: isTotal ? FontWeight.bold : FontWeight.normal, fontSize: isTotal ? 16 : 14)),
        Text(
          '${isDeduction ? '-' : ''}${formatCurrency.format(valDouble)}',
          style: TextStyle(
            fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
            color: isDeduction ? Colors.red : (isTotal ? Colors.blue : null),
            fontSize: isTotal ? 16 : 14,
          ),
        ),
      ],
    );
  }
}
