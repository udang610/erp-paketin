import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'dart:ui';
import 'package:shimmer/shimmer.dart';
import 'package:dio/dio.dart';
import '../../../core/widgets/bouncing_widget.dart';
import '../../auth/provider/auth_provider.dart';
import '../provider/profile_provider.dart';
import '../provider/timer_provider.dart';
import '../../attendance/view/check_in_screen.dart';
import '../../leave/view/leave_screen.dart';
import '../../documents/view/document_screen.dart';
import '../../approval/view/approval_screen.dart';
import '../../../core/providers/theme_provider.dart';
import '../../attendance/view/attendance_menu_screen.dart';
import '../../attendance/view/attendance_menu_tab.dart';
import '../../attendance/view/calendar_screen.dart';
import '../../team/view/team_screen.dart';
import '../../profile/view/account_settings_screen.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'camera_overlay_screen.dart';
import 'widgets/weekly_attendance_chart.dart';
import '../../payroll/view/payroll_screen.dart';
import '../../asset_request/view/asset_request_screen.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _selectedIndex = 0;

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    final List<Widget> widgetOptions = <Widget>[
      const HomeTab(),
      const AttendanceMenuTab(),
      const NotificationsTab(),
      const ProfileTab(),
    ];

    return Scaffold(
      extendBody: true, // For glassmorphism effect
      body: SafeArea(
        child: widgetOptions.elementAt(_selectedIndex),
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          boxShadow: [
            if (!isDark)
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, -5),
              ),
          ],
        ),
        child: ClipRRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: BottomNavigationBar(
              type: BottomNavigationBarType.fixed,
              backgroundColor: isDark ? const Color(0xFF1E1E1E).withOpacity(0.85) : Colors.white.withOpacity(0.85),
              elevation: 0,
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: 'Beranda',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.sensor_door_outlined),
            activeIcon: Icon(Icons.sensor_door),
            label: 'Kehadiran',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.notifications_none_outlined),
            activeIcon: Icon(Icons.notifications),
            label: 'Notifikasi',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: 'Profil',
          ),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.red[700],
        unselectedItemColor: isDark ? Colors.grey[400] : Colors.grey,
        onTap: _onItemTapped,
              ),
            ),
          ),
        ),
    );
  }
}

class HomeTab extends ConsumerWidget {
  const HomeTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SingleChildScrollView(
      child: Stack(
        children: [
          // Background Header
          Container(
            height: 240,
            decoration: BoxDecoration(
              color: Colors.red[700],
              borderRadius: const BorderRadius.only(
                bottomLeft: Radius.circular(32),
                bottomRight: Radius.circular(32),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(left: 20.0, right: 20.0, top: 40.0, bottom: 100.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          radius: 22,
                          backgroundColor: Colors.red[100],
                          child: Icon(Icons.person, color: Colors.red[700], size: 24),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Consumer(
                              builder: (context, ref, child) {
                                final profileAsync = ref.watch(profileProvider);
                                return profileAsync.when(
                                  data: (profile) {
                                    final name = profile?['full_name'] ?? 'User';
                                    return Text(
                                      name,
                                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                                    );
                                  },
                                  loading: () => Container(
                                    height: 18, width: 100, color: Colors.white24,
                                  ),
                                  error: (_, __) => const Text(
                                    'Error Loading',
                                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                                  ),
                                );
                              },
                            ),
                          ],
                        ),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.notifications_none, color: Colors.white),
                      onPressed: () {},
                    )
                  ],
                ),
                const SizedBox(height: 32),

                // Attendance Card
                Consumer(
                  builder: (context, ref, child) {
                    final checkInTime = ref.watch(checkInTimeProvider);
                    final timerAsync = ref.watch(runningTimerProvider);
                    
                    if (checkInTime == null) {
                      return BouncingWidget(
                        child: Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF2B303B) : Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              if (!isDark)
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.05),
                                  blurRadius: 16,
                                  offset: const Offset(0, 4),
                                )
                            ],
                          ),
                          child: Column(
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    _getIndonesianDay(DateTime.now()),
                                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: isDark ? Colors.white : Colors.black87),
                                  ),
                                  Text(
                                    _getIndonesianDate(DateTime.now()),
                                    style: TextStyle(color: isDark ? Colors.grey[400] : Colors.grey[600], fontSize: 13),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceAround,
                                children: [
                                  Column(
                                    children: [
                                      Text('Presensi Masuk', style: TextStyle(color: isDark ? Colors.grey[400] : Colors.grey[500], fontSize: 12)),
                                      const SizedBox(height: 4),
                                      Text('--:--', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? Colors.white : Colors.black)),
                                    ],
                                  ),
                                  Container(
                                    height: 40, width: 1,
                                    color: isDark ? Colors.grey[700] : Colors.grey[200],
                                  ),
                                  Column(
                                    children: [
                                      Text('Status', style: TextStyle(color: isDark ? Colors.grey[400] : Colors.grey[500], fontSize: 12)),
                                      const SizedBox(height: 8),
                                      ElevatedButton.icon(
                                        onPressed: () {
                                          Navigator.push(context, MaterialPageRoute(builder: (_) => const CheckInScreen()));
                                        },
                                        icon: const Icon(Icons.sensor_door_outlined, size: 16),
                                        label: const Text('Presensi', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: Colors.blue[600],
                                          foregroundColor: Colors.white,
                                          elevation: 0,
                                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
                                          minimumSize: const Size(0, 36),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    }
                    
                    final inTimeStr = DateFormat('HH:mm').format(checkInTime);
                    
                    return BouncingWidget(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF333A47) : Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            if (!isDark)
                              BoxShadow(
                                color: Colors.black.withOpacity(0.05),
                                blurRadius: 16,
                                offset: const Offset(0, 4),
                              )
                          ],
                        ),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      _getIndonesianDay(DateTime.now()),
                                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: isDark ? Colors.white : Colors.black87),
                                    ),
                                  ],
                                ),
                                Text(
                                  _getIndonesianDate(DateTime.now()),
                                  style: TextStyle(color: isDark ? Colors.grey[400] : Colors.grey[600], fontSize: 13),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            Container(
                              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
                              decoration: BoxDecoration(
                                color: isDark ? const Color(0xFF2C323D) : Colors.grey[50],
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: isDark ? Colors.grey[700]! : Colors.grey[200]!, width: 1),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      children: [
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            const Icon(Icons.sensor_door_outlined, color: Colors.blueAccent, size: 18),
                                            const SizedBox(width: 4),
                                            Text('Presensi Masuk', style: TextStyle(color: isDark ? Colors.grey[300] : Colors.grey[600], fontSize: 12)),
                                          ],
                                        ),
                                        const SizedBox(height: 12),
                                        SizedBox(
                                          height: 36,
                                          child: Center(
                                            child: Text(inTimeStr, style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: isDark ? Colors.white : Colors.black87)),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Container(height: 50, width: 1, color: isDark ? Colors.grey[700] : Colors.grey[200]),
                                  Expanded(
                                    child: Column(
                                      children: [
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            const Icon(Icons.sensor_door_outlined, color: Colors.blueAccent, size: 18),
                                            const SizedBox(width: 4),
                                            Text('Presensi Keluar', style: TextStyle(color: isDark ? Colors.grey[300] : Colors.grey[600], fontSize: 12)),
                                          ],
                                        ),
                                        const SizedBox(height: 12),
                                        SizedBox(
                                          height: 36,
                                          child: ElevatedButton(
                                          onPressed: () {
                                            // Check out action
                                            ref.read(checkInTimeProvider.notifier).state = null;
                                          },
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Colors.red[400],
                                            foregroundColor: Colors.white,
                                            elevation: 0,
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 0),
                                            minimumSize: const Size(100, 36),
                                          ),
                                          child: const Text('Keluar', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                                        ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: isDark ? Colors.grey[800] : Colors.grey[100],
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  child: Row(
                                    children: [
                                      Container(width: 6, height: 6, decoration: const BoxDecoration(color: Colors.green, shape: BoxShape.circle), margin: const EdgeInsets.only(right: 6)),
                                      Text('Presensi masuk', style: TextStyle(color: isDark ? Colors.grey[300] : Colors.grey[600], fontSize: 11)),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: isDark ? Colors.grey[800] : Colors.grey[100],
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  child: Row(
                                    children: [
                                      const Icon(Icons.access_time, color: Colors.green, size: 14),
                                      const SizedBox(width: 6),
                                      timerAsync.when(
                                        data: (val) => Text('$val yang lalu', style: TextStyle(color: isDark ? Colors.grey[300] : Colors.grey[600], fontSize: 11)),
                                        loading: () => Text('--:--:-- yang lalu', style: TextStyle(color: isDark ? Colors.grey[300] : Colors.grey[600], fontSize: 11)),
                                        error: (_, __) => Text('Error', style: TextStyle(color: isDark ? Colors.grey[300] : Colors.grey[600], fontSize: 11)),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),
                
                // Grid Menu Container
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF2B303B) : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      if (!isDark)
                        BoxShadow(
                          color: Colors.black.withOpacity(0.05),
                          blurRadius: 16,
                          offset: const Offset(0, 4),
                        )
                    ],
                  ),
                  child: GridView.count(
                    crossAxisCount: 4,
                    childAspectRatio: 0.70, // fixed overflow
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 16,
                    crossAxisSpacing: 8,
                    children: [
                      _buildGridMenu(context, Icons.fingerprint_outlined, 'Kehadiran', Colors.blue[100]!, Colors.blue[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const AttendanceMenuScreen()));
                      }),
                      _buildGridMenu(context, Icons.flight_takeoff_outlined, 'Cuti', Colors.orange[100]!, Colors.orange[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const LeaveScreen()));
                      }),
                      _buildGridMenu(context, Icons.request_quote_outlined, 'Gaji', Colors.green[100]!, Colors.green[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const PayrollScreen()));
                      }),
                      _buildGridMenu(context, Icons.inventory_2_outlined, 'Asset & ATK', Colors.indigo[100]!, Colors.indigo[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const AssetRequestScreen()));
                      }),
                      _buildGridMenu(context, Icons.check_circle_outline, 'Persetujuan', Colors.purple[100]!, Colors.purple[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const ApprovalScreen()));
                      }),
                      _buildGridMenu(context, Icons.folder_open_outlined, 'Dokumen', Colors.amber[100]!, Colors.amber[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const DocumentScreen()));
                      }),
                      _buildGridMenu(context, Icons.people_outline, 'Tim', Colors.teal[100]!, Colors.teal[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const TeamScreen()));
                      }),
                      _buildGridMenu(context, Icons.receipt_long_outlined, 'Klaim', Colors.indigo[100]!, Colors.indigo[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const DummyModuleScreen(title: 'Reimburse')));
                      }),
                      _buildGridMenu(context, Icons.calendar_month_outlined, 'Kalender', Colors.pink[100]!, Colors.pink[700]!, () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const CalendarScreen()));
                      }),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Analytics Chart
                const WeeklyAttendanceChart(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getIndonesianDay(DateTime date) {
    final days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'];
    return days[date.weekday - 1];
  }

  String _getIndonesianDate(DateTime date) {
    final months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    return '${date.day} ${months[date.month - 1]} ${date.year}';
  }

  Widget _buildGridMenu(BuildContext context, IconData icon, String label, Color bgColor, Color iconColor, VoidCallback onTap) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark ? bgColor.withOpacity(0.15) : bgColor.withOpacity(0.3),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: isDark ? bgColor.withOpacity(0.3) : bgColor.withOpacity(0.5), width: 1.5),
            ),
            child: Icon(icon, color: iconColor, size: 24),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.grey[300] : Colors.grey[800],
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

// ----------------------------------------------------------------------
// 2. Notifications Tab
// ----------------------------------------------------------------------

final notificationsProvider = FutureProvider<List<dynamic>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final authState = ref.watch(authProvider);
  if (!authState.isAuthenticated) return [];

  try {
    final response = await apiClient.dio.get('/notifications/api/messages/');
    return response.data is List ? response.data : (response.data['results'] ?? []);
  } catch (e) {
    debugPrint('Failed to load notifications: $e');
    return [];
  }
});

class NotificationsTab extends ConsumerWidget {
  const NotificationsTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifsAsync = ref.watch(notificationsProvider);

    return Padding(
      padding: const EdgeInsets.only(left: 20.0, right: 20.0, top: 20.0, bottom: 100.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Notifikasi',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: Icon(Icons.refresh, color: Colors.grey[600]),
                onPressed: () => ref.invalidate(notificationsProvider),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: notifsAsync.when(
              data: (notifs) {
                if (notifs.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.notifications_off_outlined, size: 48, color: Colors.grey[300]),
                        const SizedBox(height: 12),
                        Text('Tidak ada notifikasi', style: TextStyle(color: Colors.grey[500])),
                      ],
                    ),
                  );
                }
                return ListView.builder(
                  itemCount: notifs.length,
                  itemBuilder: (context, index) {
                    final n = notifs[index];
                    final type = n['notification_type'] ?? 'SYSTEM';
                    return _buildNotificationItem(
                      n['title'] ?? 'Notifikasi',
                      n['message'] ?? '',
                      _iconForType(type),
                      _colorForType(type),
                      n['is_read'] ?? false,
                    );
                  },
                );
              },
              loading: () => Column(
                children: List.generate(3, (i) => Shimmer.fromColors(
                  baseColor: Colors.grey[300]!,
                  highlightColor: Colors.grey[100]!,
                  child: Container(
                    height: 72,
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
                  ),
                )),
              ),
              error: (_, __) => Center(child: Text('Gagal memuat notifikasi', style: TextStyle(color: Colors.red[400]))),
            ),
          )
        ],
      ),
    );
  }

  IconData _iconForType(String type) {
    switch (type) {
      case 'ATTENDANCE': return Icons.access_time;
      case 'LEAVE': return Icons.calendar_month;
      case 'DOCUMENT': return Icons.folder_shared;
      default: return Icons.campaign;
    }
  }

  MaterialColor _colorForType(String type) {
    switch (type) {
      case 'ATTENDANCE': return Colors.green;
      case 'LEAVE': return Colors.blue;
      case 'DOCUMENT': return Colors.purple;
      default: return Colors.orange;
    }
  }

  Widget _buildNotificationItem(String title, String desc, IconData icon, MaterialColor color, bool isRead) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isRead ? Colors.white : color[50],
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isRead ? Colors.grey[200]! : color[100]!),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color[50],
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color[600], size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontWeight: isRead ? FontWeight.w500 : FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 4),
                Text(desc, style: TextStyle(color: Colors.grey[600], fontSize: 12, height: 1.3)),
              ],
            ),
          ),
          if (!isRead)
            Container(
              width: 8, height: 8,
              decoration: BoxDecoration(color: color[600], shape: BoxShape.circle),
            ),
        ],
      ),
    );
  }
}

// ----------------------------------------------------------------------
// 3. Profile Tab
// ----------------------------------------------------------------------
final aiPhotoProvider = StateProvider<bool>((ref) => false);

class ProfileTab extends ConsumerWidget {
  const ProfileTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.only(left: 20.0, right: 20.0, top: 20.0, bottom: 100.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Profil Karyawan',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 32),
            Consumer(builder: (context, ref, child) {
              final hasAiPhoto = ref.watch(aiPhotoProvider);
              return CircleAvatar(
                radius: 40,
                backgroundColor: hasAiPhoto ? Colors.transparent : Colors.red[100],
                backgroundImage: hasAiPhoto ? const AssetImage('assets/images/ai_profile_photo.png') : null,
                child: hasAiPhoto ? null : Icon(Icons.person, color: Colors.red[700], size: 40),
              );
            }),
            const SizedBox(height: 16),
            Consumer(
              builder: (context, ref, child) {
                final profileAsync = ref.watch(profileProvider);
                return profileAsync.when(
                  data: (profile) {
                    final name = profile?['full_name'] ?? 'User';
                    return Text(
                      name,
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    );
                  },
                  loading: () => Shimmer.fromColors(
                    baseColor: Colors.grey[300]!,
                    highlightColor: Colors.grey[100]!,
                    child: Container(
                      height: 24,
                      width: 120,
                      color: Colors.white,
                    ),
                  ),
                  error: (_, __) => const Text('Error', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                );
              },
            ),
            const SizedBox(height: 4),
            Consumer(
              builder: (context, ref, child) {
                final profileAsync = ref.watch(profileProvider);
                final position = profileAsync.value?['position_name'] ?? profileAsync.value?['position']?['name'] ?? 'Karyawan';
                return Text(position, style: TextStyle(color: Colors.grey[600], fontSize: 13));
              }
            ),
            
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _showPhotoUploadOptions(context, ref),
                  icon: const Icon(Icons.camera_alt, size: 16),
                  label: const Text('Ubah Foto Profil (AI)', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red[700],
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 32),
            
            // Menu List
            _buildProfileMenu(context, Icons.settings, 'Pengaturan Akun', onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const AccountSettingsScreen()));
            }),
            const Divider(),
            _buildProfileMenu(context, Icons.lock, 'Ubah Password', onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const DummyModuleScreen(title: 'Ubah Password')));
            }),
            const Divider(),
            Consumer(builder: (context, ref, child) {
              final isDark = ref.watch(themeModeProvider) == ThemeMode.dark;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4.0),
                child: Row(
                  children: [
                    Icon(Icons.dark_mode_outlined, color: Colors.grey[700], size: 22),
                    const SizedBox(width: 16),
                    const Text('Mode Gelap', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
                    const Spacer(),
                    Switch(
                      value: isDark,
                      onChanged: (val) {
                        ref.read(themeModeProvider.notifier).toggleTheme();
                      },
                      activeColor: Colors.red[700],
                    ),
                  ],
                ),
              );
            }),
            const Divider(),
            _buildProfileMenu(context, Icons.help_outline, 'Bantuan & Dukungan', onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const DummyModuleScreen(title: 'Bantuan & Dukungan')));
            }),
            const Divider(),
            
            const SizedBox(height: 32),
            
            // Dedicated Logout Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  // Call logout provider
                  ref.invalidate(checkInTimeProvider);
                  ref.read(authProvider.notifier).logout();
                },
                icon: const Icon(Icons.logout),
                label: const Text('Keluar (Logout)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red[50],
                  foregroundColor: Colors.red[700],
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileMenu(BuildContext context, IconData icon, String title, {VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap ?? () {},
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12.0),
        child: Row(
          children: [
            Icon(icon, color: Colors.grey[700], size: 22),
            const SizedBox(width: 16),
            Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
            const Spacer(),
            Icon(Icons.chevron_right, color: Colors.grey[400]),
          ],
        ),
      ),
    );
  }

  void _showPhotoUploadOptions(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (BuildContext ctx) {
        return SafeArea(
          child: Wrap(
            children: [
              const Padding(
                padding: EdgeInsets.all(16.0),
                child: Text('Pilih Sumber Foto', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('Pilih dari Galeri'),
                subtitle: const Text('Akses galeri perangkatmu, AI akan memproses foto otomatis.'),
                onTap: () async {
                  Navigator.pop(ctx);
                  final ImagePicker picker = ImagePicker();
                  final XFile? image = await picker.pickImage(source: ImageSource.gallery);
                  if (image != null && context.mounted) {
                    _simulateAIProcessing(context, ref);
                  }
                },
              ),
              ListTile(
                leading: const Icon(Icons.camera_alt),
                title: const Text('Kamera Sistem'),
                subtitle: const Text('Paskan wajah pada template panduan, AI akan sesuaikan background dan jas.'),
                onTap: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const CameraOverlayScreen()),
                  ).then((result) {
                    if (result == true && context.mounted) {
                      _simulateAIProcessing(context, ref);
                    }
                  });
                },
              ),
            ],
          ),
        );
      },
    );
  }

  void _simulateAIProcessing(BuildContext context, WidgetRef ref) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              const Text('AI sedang memproses wajah...'),
              const SizedBox(height: 8),
              Text('Menyesuaikan template jas merah & background merah', style: TextStyle(fontSize: 12, color: Colors.grey[600]), textAlign: TextAlign.center),
            ],
          ),
        );
      }
    );

    try {
      // Simulate 2 seconds of AI processing
      await Future.delayed(const Duration(seconds: 2));
      
      // Load the generated AI image from assets
      final byteData = await DefaultAssetBundle.of(context).load('assets/images/ai_profile_photo.png');
      final bytes = byteData.buffer.asUint8List();
      
      final formData = FormData.fromMap({
        'profile_picture': MultipartFile.fromBytes(bytes, filename: 'ai_profile.png'),
      });
      
      final apiClient = ref.read(apiClientProvider);
      
      // Use absolute URL to bypass baseUrl appending issues
      final String fullUrl = 'http://127.0.0.1:8000/employees/api/employees/me/';
      await apiClient.dio.patch(fullUrl, data: formData);
      
      if (context.mounted) {
        Navigator.pop(context); // Close dialog
        ref.read(aiPhotoProvider.notifier).state = true;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Foto profil berhasil diubah dan disimpan di database!')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        Navigator.pop(context); // Close dialog
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal menyimpan foto profil: $e'), backgroundColor: Colors.red[700]),
        );
      }
    }
  }
}

// ----------------------------------------------------------------------
// Dummy Placeholder Module Screen
// ----------------------------------------------------------------------
class DummyModuleScreen extends StatelessWidget {
  final String title;
  const DummyModuleScreen({Key? key, required this.title}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        elevation: 0,
      ),
      backgroundColor: Colors.grey[50],
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.construction, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              'Modul $title',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.grey[700]),
            ),
            const SizedBox(height: 8),
            Text(
              'Sedang dalam tahap pengembangan',
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            ),
          ],
        ),
      ),
    );
  }
}
