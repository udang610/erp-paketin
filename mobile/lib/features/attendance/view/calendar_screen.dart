import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:table_calendar/table_calendar.dart';
import 'attendance_history_screen.dart'; // To reuse the attendanceHistoryProvider

class CalendarScreen extends ConsumerStatefulWidget {
  const CalendarScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends ConsumerState<CalendarScreen> {
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;

  List<dynamic> _getEventsForDay(List<dynamic> events, DateTime day) {
    return events.where((event) {
      final timestampStr = event['server_timestamp'];
      if (timestampStr == null) return false;
      final dt = DateTime.tryParse(timestampStr);
      if (dt == null) return false;
      return dt.year == day.year && dt.month == day.month && dt.day == day.day;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final historyAsync = ref.watch(attendanceHistoryProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Kalender Presensi'),
      ),
      body: historyAsync.when(
        data: (events) {
          final selectedEvents = _selectedDay != null
              ? _getEventsForDay(events, _selectedDay!)
              : [];

          return Column(
            children: [
              TableCalendar(
                firstDay: DateTime.utc(2020, 1, 1),
                lastDay: DateTime.utc(2030, 12, 31),
                focusedDay: _focusedDay,
                selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
                onDaySelected: (selectedDay, focusedDay) {
                  setState(() {
                    _selectedDay = selectedDay;
                    _focusedDay = focusedDay;
                  });
                },
                eventLoader: (day) => _getEventsForDay(events, day),
                calendarStyle: CalendarStyle(
                  markerDecoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                  selectedDecoration: BoxDecoration(color: Colors.red[700], shape: BoxShape.circle),
                  todayDecoration: BoxDecoration(color: Colors.red[200]!, shape: BoxShape.circle),
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: selectedEvents.isEmpty
                    ? Center(child: Text(_selectedDay == null ? 'Pilih tanggal' : 'Tidak ada absensi di tanggal ini', style: TextStyle(color: Colors.grey[500])))
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: selectedEvents.length,
                        itemBuilder: (context, index) {
                          final ev = selectedEvents[index];
                          final type = ev['event_type'] == 'CHECK_IN' ? 'Masuk' : 'Keluar';
                          final status = ev['status'] ?? 'PRESENT';
                          final time = ev['server_timestamp'].substring(11, 16);
                          return ListTile(
                            leading: Icon(
                              type == 'Masuk' ? Icons.login : Icons.logout,
                              color: type == 'Masuk' ? Colors.green : Colors.blue,
                            ),
                            title: Text('Presensi $type'),
                            subtitle: Text('Status: $status'),
                            trailing: Text(time, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          );
                        },
                      ),
              )
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => const Center(child: Text('Gagal memuat kalender')),
      ),
    );
  }
}
