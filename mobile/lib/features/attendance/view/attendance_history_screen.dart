import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../../../core/network/api_client.dart';
import '../../auth/provider/auth_provider.dart';

final attendanceHistoryProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);
  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/hr/attendance/api/events/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Failed to load attendance history: $e');
    return [];
  }
});

class AttendanceHistoryScreen extends ConsumerWidget {
  const AttendanceHistoryScreen({Key? key}) : super(key: key);

  Color _statusBg(String status) {
    if (status == 'PRESENT') return Colors.green[50]!;
    if (status == 'LATE') return Colors.orange[50]!;
    if (status == 'PENDING') return Colors.purple[50]!;
    return Colors.grey[100]!;
  }
  
  Color _statusFg(String status) {
    if (status == 'PRESENT') return Colors.green[700]!;
    if (status == 'LATE') return Colors.orange[700]!;
    if (status == 'PENDING') return Colors.purple[700]!;
    return Colors.grey[700]!;
  }
  
  String _statusLabel(String status) {
    if (status == 'PRESENT') return 'TEPAT WAKTU';
    if (status == 'LATE') return 'TERLAMBAT';
    if (status == 'PENDING') return 'MENUNGGU';
    return status;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(attendanceHistoryProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Riwayat Presensi'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(attendanceHistoryProvider),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: historyAsync.when(
          data: (events) {
            if (events.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.event_busy, size: 48, color: Colors.grey[300]),
                    const SizedBox(height: 12),
                    Text('Belum ada riwayat presensi', style: TextStyle(color: Colors.grey[500])),
                  ],
                ),
              );
            }
            return ListView.builder(
              itemCount: events.length,
              itemBuilder: (context, index) {
                final event = events[index];
                final type = event['event_type'] ?? 'CHECK_IN';
                final status = event['status'] ?? 'PRESENT';
                final timestamp = event['server_timestamp'] ?? '';
                final time = timestamp.length >= 16 ? timestamp.substring(11, 16) : '--:--';
                final date = timestamp.length >= 10 ? timestamp.substring(0, 10) : '';
                final isCheckIn = type == 'CHECK_IN';

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF2B303B) : Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      if (!isDark)
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        )
                    ],
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: isCheckIn ? Colors.green.withOpacity(0.1) : Colors.blue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(
                          isCheckIn ? Icons.login : Icons.logout,
                          color: isCheckIn ? Colors.green : Colors.blue,
                          size: 20,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              isCheckIn ? 'Presensi Masuk' : 'Presensi Keluar',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                            const SizedBox(height: 4),
                            Text(date, style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(time, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isCheckIn ? Colors.green : Colors.blue)),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: isDark ? _statusBg(status).withOpacity(0.2) : _statusBg(status),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(_statusLabel(status), style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: _statusFg(status))),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            );
          },
          loading: () => Column(
            children: List.generate(5, (i) => Shimmer.fromColors(
              baseColor: Colors.grey[300]!,
              highlightColor: Colors.grey[100]!,
              child: Container(
                height: 70,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
              ),
            )),
          ),
          error: (_, __) => Center(child: Text('Gagal memuat riwayat', style: TextStyle(color: Colors.red[400]))),
        ),
      ),
    );
  }
}
