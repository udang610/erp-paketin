import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../../auth/provider/auth_provider.dart';

// Documents provider
final documentsProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);
  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/documents/api/files/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Failed to load documents: $e');
    return [];
  }
});

class DocumentScreen extends ConsumerWidget {
  const DocumentScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final docsAsync = ref.watch(documentsProvider);

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('Dokumen Karyawan'),
        elevation: 0,
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(documentsProvider),
        child: docsAsync.when(
          data: (docs) {
            if (docs.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.folder_open, size: 56, color: Colors.grey[300]),
                    const SizedBox(height: 12),
                    Text('Belum ada dokumen', style: TextStyle(fontSize: 15, color: Colors.grey[500])),
                    const SizedBox(height: 4),
                    Text('Dokumen Anda akan muncul di sini', style: TextStyle(fontSize: 13, color: Colors.grey[400])),
                  ],
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(20.0),
              itemCount: docs.length,
              itemBuilder: (context, index) {
                final doc = docs[index];
                return _buildDocItem(
                  doc['title'] ?? 'Dokumen',
                  doc['mime_type'] ?? 'File',
                  _iconForMime(doc['mime_type']),
                  Colors.purple,
                );
              },
            );
          },
          loading: () => ListView(
            padding: const EdgeInsets.all(20.0),
            children: List.generate(4, (i) => Shimmer.fromColors(
              baseColor: Colors.grey[300]!,
              highlightColor: Colors.grey[100]!,
              child: Container(
                height: 72,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
              ),
            )),
          ),
          error: (_, __) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
                const SizedBox(height: 12),
                const Text('Gagal memuat dokumen'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  IconData _iconForMime(String? mime) {
    if (mime == null) return Icons.insert_drive_file;
    if (mime.contains('pdf')) return Icons.picture_as_pdf;
    if (mime.contains('image')) return Icons.image;
    if (mime.contains('word') || mime.contains('document')) return Icons.description;
    if (mime.contains('sheet') || mime.contains('excel')) return Icons.table_chart;
    return Icons.insert_drive_file;
  }

  Widget _buildDocItem(String title, String size, IconData icon, MaterialColor color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color[50],
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color[700], size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 4),
                Text(size, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
              ],
            ),
          ),
          Icon(Icons.download, color: Colors.grey[400], size: 22),
        ],
      ),
    );
  }
}
