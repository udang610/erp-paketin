import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../auth/provider/auth_provider.dart';

final branchesProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  try {
    final response = await apiClient.dio.get('/organizations/api/branches/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Failed to load branches: $e');
    return [];
  }
});

class AdminSettingsScreen extends ConsumerStatefulWidget {
  const AdminSettingsScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<AdminSettingsScreen> createState() => _AdminSettingsScreenState();
}

class _AdminSettingsScreenState extends ConsumerState<AdminSettingsScreen> {
  @override
  Widget build(BuildContext context) {
    final branchesAsync = ref.watch(branchesProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Pengaturan Perusahaan (Admin)'),
        elevation: 0,
      ),
      backgroundColor: isDark ? const Color(0xFF1E2229) : Colors.grey[50],
      body: branchesAsync.when(
        data: (branches) {
          if (branches.isEmpty) {
            return const Center(child: Text('Tidak ada data cabang.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: branches.length,
            itemBuilder: (context, index) {
              final branch = branches[index];
              return Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: isDark ? Colors.grey[800]! : Colors.grey[200]!),
                ),
                color: isDark ? const Color(0xFF2B303B) : Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              '${branch['name']} (${branch['code']})',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.edit, color: Colors.blue),
                            onPressed: () => _showEditDialog(context, branch),
                          )
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text('Alamat: ${branch['address']}'),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Icon(Icons.location_on, size: 16, color: Colors.red[700]),
                          const SizedBox(width: 4),
                          Text('Radius Absen: ${branch['attendance_radius_meters']} meter'),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(Icons.access_time, size: 16, color: Colors.orange[700]),
                          const SizedBox(width: 4),
                          Text('Jam Masuk: ${branch['clock_in_time']} | Jam Keluar: ${branch['clock_out_time']}'),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Gagal memuat: $err')),
      ),
    );
  }

  void _showEditDialog(BuildContext context, Map<String, dynamic> branch) {
    final radiusCtrl = TextEditingController(text: branch['attendance_radius_meters']?.toString() ?? '200');
    final clockInCtrl = TextEditingController(text: branch['clock_in_time'] ?? '08:00:00');
    final clockOutCtrl = TextEditingController(text: branch['clock_out_time'] ?? '17:00:00');

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text('Edit ${branch['name']}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: radiusCtrl,
                  decoration: const InputDecoration(labelText: 'Radius Absen (meter)'),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: clockInCtrl,
                  decoration: const InputDecoration(labelText: 'Jam Masuk (HH:MM:SS)'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: clockOutCtrl,
                  decoration: const InputDecoration(labelText: 'Jam Keluar (HH:MM:SS)'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Batal')),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(ctx);
                await _updateBranch(
                  branch['id'],
                  int.tryParse(radiusCtrl.text) ?? 200,
                  clockInCtrl.text,
                  clockOutCtrl.text,
                );
              },
              child: const Text('Simpan'),
            ),
          ],
        );
      }
    );
  }

  Future<void> _updateBranch(String id, int radius, String clockIn, String clockOut) async {
    final apiClient = ref.read(apiClientProvider);
    try {
      await apiClient.dio.patch('/organizations/api/branches/$id/', data: {
        'attendance_radius_meters': radius,
        'clock_in_time': clockIn,
        'clock_out_time': clockOut,
      });
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Berhasil diperbarui!')));
      ref.invalidate(branchesProvider);
    } catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Gagal memperbarui: $e'), backgroundColor: Colors.red));
    }
  }
}
