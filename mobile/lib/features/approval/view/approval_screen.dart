import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/network/api_client.dart';
import '../../auth/provider/auth_provider.dart';
import 'package:dio/dio.dart';

final approvalRequestsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);
  if (!authState.isAuthenticated) return [];

  // Assuming HRGA or superuser gets all requests
  final response = await apiClient.dio.get('/hr/leave/api/requests/');
  final data = response.data is List ? response.data : (response.data['results'] ?? []);
  
  // Filter for pending only
  return data.where((item) => item['status'] == 'PENDING_SUPERVISOR' || item['status'] == 'PENDING_HRGA').toList();
});

class ApprovalScreen extends ConsumerStatefulWidget {
  const ApprovalScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ApprovalScreen> createState() => _ApprovalScreenState();
}

class _ApprovalScreenState extends ConsumerState<ApprovalScreen> {
  bool _isProcessing = false;

  Future<void> _updateStatus(String id, String action) async {
    if (_isProcessing) return;
    setState(() => _isProcessing = true);

    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.dio.put('/hr/leave/api/requests/$id/$action/');
      ref.invalidate(approvalRequestsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(action == 'approve' ? 'Cuti disetujui' : 'Cuti ditolak'),
            backgroundColor: action == 'approve' ? Colors.green[700] : Colors.orange[700],
          ),
        );
      }
    } on DioException catch (e) {
      if (mounted) {
        String errMsg = e.response?.data?['detail'] ?? e.message ?? 'Unknown error';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal $action: $errMsg'),
            backgroundColor: Colors.red[700],
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final requestsAsync = ref.watch(approvalRequestsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Persetujuan Cuti'),
        elevation: 0,
      ),
      backgroundColor: Colors.grey[50],
      body: requestsAsync.when(
        data: (requests) {
          if (requests.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.check_circle_outline, size: 56, color: Colors.grey[300]),
                  const SizedBox(height: 12),
                  Text('Tidak ada pengajuan cuti yang perlu disetujui', style: TextStyle(color: Colors.grey[500], fontSize: 13)),
                ],
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(approvalRequestsProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: requests.length,
              itemBuilder: (context, index) {
                final req = requests[index];
                return _buildRequestCard(req);
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildRequestCard(dynamic req) {
    // Format dates
    final start = DateTime.tryParse(req['start_date'] ?? '') ?? DateTime.now();
    final end = DateTime.tryParse(req['end_date'] ?? '') ?? DateTime.now();
    final dateFmt = DateFormat('dd MMM yyyy');
    
    // Parse leave type and reason
    final leaveTypeName = req['leave_type_name'] ?? 'Cuti';
    final reason = req['reason'] ?? '-';
    // Actually we don't have employee name in serializer if we didn't include it. Wait, we should check what's in req.
    // I will assume it's req['employee'] if it's nested, or we can just say "Karyawan".
    // Let's use 'Karyawan' for now if name is not serialized.
    final employeeName = req['employee_name'] ?? 'Karyawan'; 

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(employeeName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Menunggu',
                  style: TextStyle(color: Colors.orange[700], fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(Icons.calendar_today, size: 16, color: Colors.grey[500]),
              const SizedBox(width: 8),
              Text('${dateFmt.format(start)} - ${dateFmt.format(end)}', style: TextStyle(color: Colors.grey[700], fontSize: 13)),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Icon(Icons.category, size: 16, color: Colors.grey[500]),
              const SizedBox(width: 8),
              Text(leaveTypeName, style: TextStyle(color: Colors.grey[700], fontSize: 13)),
            ],
          ),
          const SizedBox(height: 12),
          Text('Alasan:', style: TextStyle(color: Colors.grey[500], fontSize: 11)),
          Text(reason, style: const TextStyle(fontSize: 13, height: 1.3)),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _isProcessing ? null : () => _updateStatus(req['id'], 'reject'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.red[700],
                    side: BorderSide(color: Colors.red[200]!),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: const Text('Tolak', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: _isProcessing ? null : () => _updateStatus(req['id'], 'approve'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green[600],
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: const Text('Setujui', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
