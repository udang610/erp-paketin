import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final checkInTimeProvider = StateProvider<DateTime?>((ref) => null);

final runningTimerProvider = StreamProvider<String>((ref) {
  final checkInTime = ref.watch(checkInTimeProvider);
  if (checkInTime == null) return Stream.value('00:00:00');
  
  return Stream.periodic(const Duration(seconds: 1), (_) {
    final diff = DateTime.now().difference(checkInTime);
    final h = diff.inHours.toString().padLeft(2, '0');
    final m = (diff.inMinutes % 60).toString().padLeft(2, '0');
    final s = (diff.inSeconds % 60).toString().padLeft(2, '0');
    return '$h:$m:$s';
  });
});
