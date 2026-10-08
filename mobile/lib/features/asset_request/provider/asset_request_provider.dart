import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../auth/provider/auth_provider.dart';
import 'package:dio/dio.dart';

final assetItemsProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);

  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/hr/asset_request/api/items/');
    if (response.data is List) {
      return response.data;
    } else if (response.data['results'] != null) {
      return response.data['results'];
    }
    return [];
  } catch (e) {
    throw Exception('Gagal memuat item aset: $e');
  }
});

final assetTransactionsProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);

  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/hr/asset_request/api/transactions/');
    if (response.data is List) {
      return response.data;
    } else if (response.data['results'] != null) {
      return response.data['results'];
    }
    return [];
  } catch (e) {
    throw Exception('Gagal memuat riwayat pengajuan: $e');
  }
});

class AssetRequestNotifier extends StateNotifier<AsyncValue<void>> {
  AssetRequestNotifier(this.ref) : super(const AsyncValue.data(null));

  final Ref ref;

  Future<void> submitRequest({
    required int itemId,
    required int quantity,
    required String reason,
    String? photoPath,
    String? signaturePath,
  }) async {
    state = const AsyncValue.loading();
    try {
      final apiClient = ref.read(apiClientProvider);
      
      FormData formData = FormData.fromMap({
        'item': itemId,
        'quantity': quantity,
        'reason': reason,
      });

      if (photoPath != null) {
        formData.files.add(
          MapEntry('photo_proof', await MultipartFile.fromFile(photoPath, filename: 'photo.jpg'))
        );
      }
      
      if (signaturePath != null) {
        formData.files.add(
          MapEntry('signature', await MultipartFile.fromFile(signaturePath, filename: 'signature.png'))
        );
      }

      await apiClient.dio.post('/hr/asset_request/api/transactions/', data: formData);
      
      // refresh transactions
      ref.invalidate(assetTransactionsProvider);
      state = const AsyncValue.data(null);
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
    }
  }
}

final assetRequestControllerProvider = StateNotifierProvider<AssetRequestNotifier, AsyncValue<void>>((ref) {
  return AssetRequestNotifier(ref);
});
