import 'dart:math';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../core/widgets/bouncing_widget.dart';
import 'check_in_screen.dart';
import 'attendance_history_screen.dart';
import 'attendance_stats_screen.dart';

class AttendanceMenuTab extends StatelessWidget {
  const AttendanceMenuTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.only(left: 20.0, right: 20.0, top: 40.0, bottom: 100.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Quick Stats Summary
            _buildQuickStatsRow(isDark),
            const SizedBox(height: 16),
            
            // Mini attendance chart
            _buildAttendanceOverviewChart(context, isDark),
            const SizedBox(height: 24),

            _buildSectionTitle('Kantor (Office)'),
            _buildMenuCard(
              context,
              icon: Icons.login,
              title: 'Presensi Masuk (Clock In)',
              subtitle: 'Lakukan absensi masuk dari lokasi kantor',
              color: Colors.green,
              onTap: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const CheckInScreen()));
              }
            ),
            _buildMenuCard(
              context,
              icon: Icons.logout,
              title: 'Presensi Keluar (Clock Out)',
              subtitle: 'Lakukan absensi pulang dari lokasi kantor',
              color: Colors.blue,
              onTap: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const CheckInScreen()));
              }
            ),

            const SizedBox(height: 24),
            _buildSectionTitle('Di Luar Kantor (Outside Office)'),
            _buildMenuCard(
              context,
              icon: Icons.map,
              title: 'Absen Dimana Saja',
              subtitle: 'Absensi jika sedang ditugaskan ke luar (Wajib Persetujuan)',
              color: Colors.orange,
              onTap: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const CheckInScreen()));
              }
            ),

            const SizedBox(height: 24),
            _buildSectionTitle('Laporan & Riwayat'),
            _buildMenuCard(
              context,
              icon: Icons.bar_chart,
              title: 'Rangkuman Presensi',
              subtitle: 'Lihat ringkasan kehadiran bulan ini',
              color: Colors.purple,
              onTap: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const AttendanceStatsScreen()));
              }
            ),
            _buildMenuCard(
              context,
              icon: Icons.history,
              title: 'Riwayat Presensi',
              subtitle: 'Lihat seluruh riwayat jam dan lokasi absensi',
              color: Colors.teal,
              onTap: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const AttendanceHistoryScreen()));
              }
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Text(
        title,
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.grey),
      ),
    );
  }

  Widget _buildMenuCard(BuildContext context, {required IconData icon, required String title, required String subtitle, required MaterialColor color, required VoidCallback onTap}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return BouncingWidget(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF2B303B) : Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            if (!isDark)
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 8,
                offset: const Offset(0, 2),
              )
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isDark ? color.withOpacity(0.2) : color[50],
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: isDark ? color[300] : color[700], size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 4),
                  Text(subtitle, style: TextStyle(color: Colors.grey[500], fontSize: 11)),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: Colors.grey[400]),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickStatsRow(bool isDark) {
    return Row(
      children: [
        _buildQuickStatItem('Hadir', '17', Icons.check_circle_outline, Colors.green, isDark),
        const SizedBox(width: 10),
        _buildQuickStatItem('Terlambat', '1', Icons.access_time, Colors.orange, isDark),
        const SizedBox(width: 10),
        _buildQuickStatItem('Izin', '1', Icons.event_busy, Colors.blue, isDark),
        const SizedBox(width: 10),
        _buildQuickStatItem('Absen', '0', Icons.cancel_outlined, Colors.red, isDark),
      ],
    );
  }

  Widget _buildQuickStatItem(String label, String value, IconData icon, MaterialColor color, bool isDark) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 6),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF2B303B) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            if (!isDark)
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
          ],
        ),
        child: Column(
          children: [
            Icon(icon, color: color[600], size: 20),
            const SizedBox(height: 6),
            Text(value, style: TextStyle(
              fontSize: 18, fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black87,
            )),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 9, color: Colors.grey[500], fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }

  Widget _buildAttendanceOverviewChart(BuildContext context, bool isDark) {
    final random = Random(DateTime.now().month);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF2B303B) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          if (!isDark)
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Tren Jam Masuk', style: TextStyle(
                fontSize: 14, fontWeight: FontWeight.bold,
                color: isDark ? Colors.white : Colors.black87,
              )),
              GestureDetector(
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const AttendanceStatsScreen()));
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: isDark ? Colors.red[900]!.withOpacity(0.3) : Colors.red[50],
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text('Lihat Detail →', style: TextStyle(
                    fontSize: 10, fontWeight: FontWeight.w600, color: Colors.red[700],
                  )),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 150,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 10,
                  getDrawingHorizontalLine: (value) => FlLine(
                    color: isDark ? Colors.white10 : Colors.grey[200]!,
                    strokeWidth: 1,
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 22,
                      getTitlesWidget: (value, meta) {
                        const days = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];
                        if (value.toInt() >= 0 && value.toInt() < days.length) {
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(days[value.toInt()],
                              style: TextStyle(fontSize: 10, color: Colors.grey[500]),
                            ),
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                minY: 465,
                maxY: 510,
                extraLinesData: ExtraLinesData(
                  horizontalLines: [
                    HorizontalLine(
                      y: 480,
                      color: Colors.green.withOpacity(0.4),
                      strokeWidth: 1.5,
                      dashArray: [8, 4],
                    ),
                  ],
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: List.generate(7, (i) {
                      return FlSpot(i.toDouble(), (478 + random.nextInt(22)).toDouble());
                    }),
                    isCurved: true,
                    curveSmoothness: 0.3,
                    color: Colors.red[400]!,
                    barWidth: 2.5,
                    isStrokeCapRound: true,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, percent, barData, index) {
                        final isLate = spot.y > 480;
                        return FlDotCirclePainter(
                          radius: 3.5,
                          color: isLate ? Colors.orange : Colors.green,
                          strokeWidth: 1.5,
                          strokeColor: Colors.white,
                        );
                      },
                    ),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.red[400]!.withOpacity(0.2),
                          Colors.red[400]!.withOpacity(0.0),
                        ],
                      ),
                    ),
                  ),
                ],
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipItems: (touchedSpots) {
                      return touchedSpots.map((spot) {
                        final h = (spot.y ~/ 60).toString().padLeft(2, '0');
                        final m = (spot.y.toInt() % 60).toString().padLeft(2, '0');
                        return LineTooltipItem(
                          '$h:$m',
                          const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                        );
                      }).toList();
                    },
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(width: 10, height: 2, color: Colors.green.withOpacity(0.5)),
              const SizedBox(width: 4),
              Text('Target 08:00', style: TextStyle(fontSize: 9, color: Colors.grey[500])),
              const SizedBox(width: 16),
              Container(width: 10, height: 2, color: Colors.red[400]),
              const SizedBox(width: 4),
              Text('Jam Masuk', style: TextStyle(fontSize: 9, color: Colors.grey[500])),
            ],
          ),
        ],
      ),
    );
  }
}
