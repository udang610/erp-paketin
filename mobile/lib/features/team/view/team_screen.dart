import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../../../core/network/api_client.dart';
import '../../auth/provider/auth_provider.dart';

final teamProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  try {
    // Actually using the generic /employees/api/employees/ endpoint to list all
    final response = await apiClient.dio.get('/employees/api/employees/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Error loading team: $e');
    return [];
  }
});

class TeamScreen extends ConsumerWidget {
  const TeamScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final teamAsync = ref.watch(teamProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tim'),
      ),
      body: teamAsync.when(
        data: (team) {
          if (team.isEmpty) {
            return const Center(child: Text('Belum ada data karyawan.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: team.length,
            itemBuilder: (context, index) {
              final emp = team[index];
              return Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: Colors.grey[200]!),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  leading: const CircleAvatar(
                    backgroundColor: Colors.red,
                    child: Icon(Icons.person, color: Colors.white),
                  ),
                  title: Text(emp['full_name'] ?? 'Anonim', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(emp['position']?['title'] ?? emp['department']?['name'] ?? 'Karyawan'),
                  trailing: const Icon(Icons.chat_bubble_outline, color: Colors.grey),
                ),
              );
            },
          );
        },
        loading: () => ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: 5,
          itemBuilder: (context, index) => Shimmer.fromColors(
            baseColor: Colors.grey[300]!,
            highlightColor: Colors.grey[100]!,
            child: Container(
              height: 70,
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        error: (_, __) => const Center(child: Text('Gagal memuat daftar tim')),
      ),
    );
  }
}
