import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../../auth/provider/auth_provider.dart';

// Leave balance provider
final leaveBalanceProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);
  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/hr/leave/api/balances/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Failed to load leave balances: $e');
    return [];
  }
});

// Leave requests provider
final leaveRequestsProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);
  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/hr/leave/api/requests/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Failed to load leave requests: $e');
    return [];
  }
});

class LeaveScreen extends ConsumerWidget {
  const LeaveScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balancesAsync = ref.watch(leaveBalanceProvider);
    final requestsAsync = ref.watch(leaveRequestsProvider);

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('Pengajuan Cuti'),
        elevation: 0,
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(leaveBalanceProvider);
          ref.invalidate(leaveRequestsProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Leave Balance Card
              balancesAsync.when(
                data: (balances) {
                  if (balances.isEmpty) {
                    return Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.blue[50],
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.calendar_month, color: Colors.blue[700], size: 28),
                          const SizedBox(width: 16),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Sisa Cuti Tahunan', style: TextStyle(color: Colors.blueGrey, fontSize: 12)),
                              const SizedBox(height: 4),
                              Text('12 Hari', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.blue[900])),
                            ],
                          ),
                        ],
                      ),
                    );
                  }
                  // Show first balance
                  final b = balances[0];
                  final remaining = b['remaining_days'] ?? (b['allocated_days'] - b['used_days']);
                  return Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.calendar_month, color: Colors.blue[700], size: 28),
                        const SizedBox(width: 16),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(b['leave_type_name'] ?? 'Cuti Tahunan', style: const TextStyle(color: Colors.blueGrey, fontSize: 12)),
                            const SizedBox(height: 4),
                            Text('$remaining Hari', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.blue[900])),
                          ],
                        ),
                      ],
                    ),
                  );
                },
                loading: () => Shimmer.fromColors(
                  baseColor: Colors.grey[300]!,
                  highlightColor: Colors.grey[100]!,
                  child: Container(
                    height: 80,
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
                  ),
                ),
                error: (_, __) => Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.red[50], borderRadius: BorderRadius.circular(16)),
                  child: const Text('Gagal memuat data sisa cuti'),
                ),
              ),

              const SizedBox(height: 24),
              const Text('Menu Cuti & Izin', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildQuickMenu(context, Icons.beach_access, 'Cuti Tahunan', Colors.blue, 'Cuti Tahunan'),
                  _buildQuickMenu(context, Icons.time_to_leave, 'Izin', Colors.orange, 'Izin'),
                  _buildQuickMenu(context, Icons.local_hospital, 'Sakit', Colors.red, 'Sakit'),
                ],
              ),

              const SizedBox(height: 24),
              const Text('Riwayat Pengajuan', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),

              // Leave Requests List
              requestsAsync.when(
                data: (requests) {
                  if (requests.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(32.0),
                        child: Column(
                          children: [
                            Icon(Icons.inbox_outlined, size: 48, color: Colors.grey[300]),
                            const SizedBox(height: 12),
                            Text('Belum ada pengajuan cuti', style: TextStyle(color: Colors.grey[500])),
                          ],
                        ),
                      ),
                    );
                  }
                  return Column(
                    children: requests.map<Widget>((r) {
                      final status = r['status'] ?? 'PENDING';
                      final statusLabel = _statusLabel(status);
                      final statusColor = _statusColor(status);
                      return _buildLeaveItem(
                        r['leave_type_name'] ?? 'Cuti',
                        '${r['start_date']} s/d ${r['end_date']}',
                        statusLabel,
                        statusColor,
                      );
                    }).toList(),
                  );
                },
                loading: () => Column(
                  children: List.generate(3, (i) => Shimmer.fromColors(
                    baseColor: Colors.grey[300]!,
                    highlightColor: Colors.grey[100]!,
                    child: Container(
                      height: 72,
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                    ),
                  )),
                ),
                error: (_, __) => const Text('Gagal memuat riwayat cuti'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildQuickMenu(BuildContext context, IconData icon, String label, MaterialColor color, String leaveType) {
    return GestureDetector(
      onTap: () {
        Navigator.push(context, MaterialPageRoute(builder: (_) => LeaveFormScreen(initialType: leaveType)));
      },
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: color[50],
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color[700], size: 28),
          ),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'APPROVED': return 'Disetujui';
      case 'REJECTED': return 'Ditolak';
      case 'CANCELLED': return 'Dibatalkan';
      case 'PENDING_SUPERVISOR': return 'Menunggu Atasan';
      case 'PENDING_HRGA': return 'Menunggu HR';
      default: return 'Diproses';
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'APPROVED': return Colors.green;
      case 'REJECTED': return Colors.red;
      case 'CANCELLED': return Colors.grey;
      default: return Colors.orange;
    }
  }

  Widget _buildLeaveItem(String title, String date, String status, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                const SizedBox(height: 4),
                Text(date, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(status, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
          )
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------
// Leave Application Form
// ---------------------------------------------------------------
class LeaveFormScreen extends ConsumerStatefulWidget {
  final String? initialType;
  const LeaveFormScreen({Key? key, this.initialType}) : super(key: key);

  @override
  ConsumerState<LeaveFormScreen> createState() => _LeaveFormScreenState();
}

class _LeaveFormScreenState extends ConsumerState<LeaveFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late String _leaveType;
  final _reasonController = TextEditingController();
  DateTime? _startDate;
  DateTime? _endDate;
  bool _isSubmitting = false;

  final List<String> _leaveTypes = ['Cuti Tahunan', 'Izin', 'Sakit', 'Lainnya'];

  @override
  void initState() {
    super.initState();
    _leaveType = widget.initialType ?? 'Cuti Tahunan';
  }

  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  int get _totalDays {
    if (_startDate == null || _endDate == null) return 0;
    return _endDate!.difference(_startDate!).inDays + 1;
  }

  Future<void> _pickDate({required bool isStart}) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() {
        if (isStart) {
          _startDate = picked;
          if (_endDate != null && _endDate!.isBefore(picked)) _endDate = picked;
        } else {
          _endDate = picked;
        }
      });
    }
  }

  Future<void> _submit() async {
    if (_startDate == null || _endDate == null || _reasonController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Harap lengkapi semua field'), backgroundColor: Colors.orange),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.dio.post('/hr/leave/api/requests/', data: {
        'start_date': _startDate!.toIso8601String().substring(0, 10),
        'end_date': _endDate!.toIso8601String().substring(0, 10),
        'total_days': _totalDays,
        'reason': _reasonController.text,
        'leave_type_name': _leaveType, // pass the leave type
      });

      if (mounted) {
        ref.invalidate(leaveRequestsProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: const Text('Pengajuan cuti berhasil dikirim!'), backgroundColor: Colors.green[700]),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal mengirim: $e'), backgroundColor: Colors.red[700]),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'Pilih Tanggal';
    return '${date.day}/${date.month}/${date.year}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('Form Pengajuan Cuti'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Type Selection
            const Text('Jenis Cuti/Izin', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _leaveType,
              decoration: InputDecoration(
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey[300]!)),
                enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey[300]!)),
              ),
              items: _leaveTypes.map((type) => DropdownMenuItem(value: type, child: Text(type))).toList(),
              onChanged: (val) {
                if (val != null) setState(() => _leaveType = val);
              },
            ),

            const SizedBox(height: 20),
            // Date Selection
            const Text('Tanggal Mulai', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () => _pickDate(isStart: true),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: Row(
                  children: [
                    Icon(Icons.calendar_today, color: Colors.blue[700], size: 20),
                    const SizedBox(width: 12),
                    Text(_formatDate(_startDate), style: TextStyle(color: _startDate != null ? Colors.black : Colors.grey)),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),
            const Text('Tanggal Selesai', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () => _pickDate(isStart: false),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: Row(
                  children: [
                    Icon(Icons.calendar_today, color: Colors.blue[700], size: 20),
                    const SizedBox(width: 12),
                    Text(_formatDate(_endDate), style: TextStyle(color: _endDate != null ? Colors.black : Colors.grey)),
                  ],
                ),
              ),
            ),

            if (_totalDays > 0) ...[
              const SizedBox(height: 12),
              Text('Total: $_totalDays hari', style: TextStyle(color: Colors.blue[700], fontWeight: FontWeight.bold)),
            ],

            const SizedBox(height: 20),
            const Text('Alasan', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            TextField(
              controller: _reasonController,
              maxLines: 4,
              decoration: InputDecoration(
                hintText: 'Masukkan alasan pengajuan cuti...',
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey[300]!)),
                enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey[300]!)),
              ),
            ),

            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue[700],
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  disabledBackgroundColor: Colors.grey[300],
                ),
                child: _isSubmitting
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('KIRIM PENGAJUAN', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
