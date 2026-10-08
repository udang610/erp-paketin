import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/provider/auth_provider.dart';

final profileProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);

  if (!authState.isAuthenticated) return null;

  try {
    // Request employee profile
    final String fullUrl = 'http://127.0.0.1:8000/employees/api/employees/me/';
    final response = await apiClient.dio.get(fullUrl);
    return response.data as Map<String, dynamic>;
  } catch (e) {
    print('Failed to load profile: $e');
    return null;
  }
});
