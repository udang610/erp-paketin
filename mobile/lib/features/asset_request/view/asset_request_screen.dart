import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../provider/asset_request_provider.dart';

class AssetRequestScreen extends ConsumerStatefulWidget {
  const AssetRequestScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<AssetRequestScreen> createState() => _AssetRequestScreenState();
}

class _AssetRequestScreenState extends ConsumerState<AssetRequestScreen> {
  @override
  Widget build(BuildContext context) {
    final transactionsAsync = ref.watch(assetTransactionsProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Asset & ATK'),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const AssetRequestFormScreen()));
        },
        child: const Icon(Icons.add),
      ),
      body: transactionsAsync.when(
        data: (transactions) {
          if (transactions.isEmpty) {
            return const Center(child: Text('Belum ada riwayat pengajuan aset.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: transactions.length,
            itemBuilder: (context, index) {
              final trx = transactions[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.blue[100],
                    child: const Icon(Icons.inventory_2, color: Colors.blue),
                  ),
                  title: Text(trx['item_name'] ?? 'Item', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('Jumlah: ${trx['quantity']} | Status: ${trx['status']}'),
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
              height: 80,
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        error: (err, _) => Center(child: Text(err.toString())),
      ),
    );
  }
}

class AssetRequestFormScreen extends ConsumerStatefulWidget {
  const AssetRequestFormScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<AssetRequestFormScreen> createState() => _AssetRequestFormScreenState();
}

class _AssetRequestFormScreenState extends ConsumerState<AssetRequestFormScreen> {
  int? _selectedItemId;
  final _quantityController = TextEditingController(text: '1');
  final _reasonController = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    final itemsAsync = ref.watch(assetItemsProvider);
    final isSubmitting = ref.watch(assetRequestControllerProvider).isLoading;

    return Scaffold(
      appBar: AppBar(title: const Text('Pengajuan Barang')),
      body: itemsAsync.when(
        data: (items) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Pilih Barang', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                  value: _selectedItemId,
                  decoration: const InputDecoration(border: OutlineInputBorder()),
                  items: items.map<DropdownMenuItem<int>>((item) {
                    return DropdownMenuItem<int>(
                      value: item['id'],
                      child: Text('${item['name']} (Stok: ${item['stock']})'),
                    );
                  }).toList(),
                  onChanged: (val) {
                    setState(() {
                      _selectedItemId = val;
                    });
                  },
                ),
                const SizedBox(height: 16),
                const Text('Jumlah', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _quantityController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(border: OutlineInputBorder()),
                ),
                const SizedBox(height: 16),
                const Text('Alasan / Keperluan', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _reasonController,
                  maxLines: 3,
                  decoration: const InputDecoration(border: OutlineInputBorder()),
                ),
                const SizedBox(height: 16),
                // (Optional: add image picker for photo and signature pad)
                const Text('Upload Foto Bukti & TTD (Bisa disusul)', style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: isSubmitting ? null : () async {
                      if (_selectedItemId == null) return;
                      await ref.read(assetRequestControllerProvider.notifier).submitRequest(
                        itemId: _selectedItemId!,
                        quantity: int.tryParse(_quantityController.text) ?? 1,
                        reason: _reasonController.text,
                      );
                      if (!mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Pengajuan berhasil!')));
                      Navigator.pop(context);
                    },
                    child: isSubmitting ? const CircularProgressIndicator(color: Colors.white) : const Text('Ajukan'),
                  ),
                )
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text(err.toString())),
      ),
    );
  }
}
