import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../auth/provider/auth_provider.dart';

final payslipListProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);

  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/hr/payroll/api/payslips/');
    if (response.data is List) {
      return response.data;
    } else if (response.data['results'] != null) {
      return response.data['results'];
    }
    return [];
  } catch (e) {
    throw Exception('Gagal memuat data slip gaji: $e');
  }
});
