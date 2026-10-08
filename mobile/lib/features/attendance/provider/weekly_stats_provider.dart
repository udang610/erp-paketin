import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/provider/auth_provider.dart';
import 'package:flutter/foundation.dart';

final weeklyStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  try {
    final response = await apiClient.dio.get('/hr/attendance/api/events/stats/');
    return response.data as Map<String, dynamic>;
  } catch (e) {
    debugPrint('Failed to load weekly stats: $e');
    return {
      'hadir': 0,
      'terlambat': 0,
      'izin': 0,
      'chart_data': []
    };
  }
});
