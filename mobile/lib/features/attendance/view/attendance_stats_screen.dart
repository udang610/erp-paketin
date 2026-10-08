import 'dart:math';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'attendance_history_screen.dart'; // To get the provider

class AttendanceStatsScreen extends ConsumerStatefulWidget {
  const AttendanceStatsScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<AttendanceStatsScreen> createState() => _AttendanceStatsScreenState();
}

class _AttendanceStatsScreenState extends ConsumerState<AttendanceStatsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _selectedMonth = 'Agustus 2026';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Statistik Kehadiran', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        centerTitle: true,
        backgroundColor: Colors.red[700],
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Month selector & Tab bar
          Container(
            color: Colors.red[700],
            child: Column(
              children: [
                // Month selector
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.chevron_left, color: Colors.white),
                        onPressed: () {},
                      ),
                      Text(
                        _selectedMonth,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.chevron_right, color: Colors.white),
                        onPressed: () {},
                      ),
                    ],
                  ),
                ),
                // Tab bar
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 20),
                  decoration: BoxDecoration(
                    color: Colors.red[800],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    labelColor: Colors.red[700],
                    unselectedLabelColor: Colors.white70,
                    labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                    unselectedLabelStyle: const TextStyle(fontSize: 12),
                    indicator: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    indicatorSize: TabBarIndicatorSize.tab,
                    dividerColor: Colors.transparent,
                    tabs: const [
                      Tab(text: 'Harian'),
                      Tab(text: 'Mingguan'),
                      Tab(text: 'Bulanan'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),

          // Content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildDailyView(isDark),
                _buildWeeklyView(isDark),
                _buildMonthlyView(isDark),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // =========== DAILY VIEW ===========
  Widget _buildDailyView(bool isDark) {
    final historyAsync = ref.watch(attendanceHistoryProvider);
    int totalHadir = 0;
    int totalTerlambat = 0;
    
    if (historyAsync.hasValue) {
      final events = historyAsync.value ?? [];
      for (var event in events) {
        if (event['event_type'] == 'CHECK_IN') {
           if (event['status'] == 'PRESENT') totalHadir++;
           if (event['status'] == 'LATE') totalTerlambat++;
        }
      }
    }
    
    final random = Random(42);
    // Generate data points for each hour (08:00 - 17:00)
    final List<FlSpot> hoursWorked = List.generate(10, (i) {
      return FlSpot(i.toDouble(), (random.nextDouble() * 2 + 6).clamp(0, 9));
    });

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary cards
          Row(
            children: [
              _buildStatCard('Total Hadir', '${totalHadir + totalTerlambat}', Icons.check_circle, Colors.blue, isDark),
              const SizedBox(width: 12),
              _buildStatCard('Tepat Waktu', '$totalHadir', Icons.timer, Colors.green, isDark),
              const SizedBox(width: 12),
              _buildStatCard('Terlambat', '$totalTerlambat', Icons.warning, Colors.orange, isDark),
            ],
          ),
          const SizedBox(height: 20),

          // Daily check-in chart
          _buildChartContainer(
            title: 'Jam Masuk Harian',
            subtitle: 'Rata-rata: 08:05',
            isDark: isDark,
            child: SizedBox(
              height: 180,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  barTouchData: BarTouchData(
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        final days = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                          '11', '12', '13', '14', '15', '16', '17', '18', '19'];
                        return BarTooltipItem(
                          'Hari ${days[group.x]}\n',
                          const TextStyle(color: Colors.white, fontSize: 11),
                          children: [
                            TextSpan(
                              text: '08:0${random.nextInt(9)}',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                          ],
                        );
                      },
                    ),
                  ),
                  titlesData: FlTitlesData(
                    leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() % 3 == 0) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(
                                '${value.toInt() + 1}',
                                style: TextStyle(fontSize: 9, color: Colors.grey[500]),
                              ),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                  ),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 2,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: isDark ? Colors.white10 : Colors.grey[200]!,
                      strokeWidth: 1,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: List.generate(19, (i) {
                    final isLate = random.nextDouble() < 0.15;
                    return BarChartGroupData(
                      x: i,
                      barRods: [
                        BarChartRodData(
                          toY: (random.nextDouble() * 4 + 5),
                          width: 8,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                          gradient: LinearGradient(
                            begin: Alignment.bottomCenter,
                            end: Alignment.topCenter,
                            colors: isLate
                                ? [Colors.orange[300]!, Colors.orange[600]!]
                                : [Colors.green[300]!, Colors.green[600]!],
                          ),
                        ),
                      ],
                    );
                  }),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Attendance pie chart
          _buildChartContainer(
            title: 'Ringkasan Status',
            subtitle: 'Bulan Ini',
            isDark: isDark,
            child: SizedBox(
              height: 160,
              child: Row(
                children: [
                  Expanded(
                    child: PieChart(
                      PieChartData(
                        sectionsSpace: 3,
                        centerSpaceRadius: 30,
                        sections: [
                          PieChartSectionData(
                            value: 17,
                            title: '89%',
                            titleStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                            color: Colors.green[500]!,
                            radius: 35,
                          ),
                          PieChartSectionData(
                            value: 1,
                            title: '5%',
                            titleStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                            color: Colors.orange[500]!,
                            radius: 30,
                          ),
                          PieChartSectionData(
                            value: 1,
                            title: '5%',
                            titleStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                            color: Colors.red[500]!,
                            radius: 30,
                          ),
                        ],
                      ),
                    ),
                  ),
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildPieLegend('Hadir (17)', Colors.green[500]!),
                      const SizedBox(height: 8),
                      _buildPieLegend('Terlambat (1)', Colors.orange[500]!),
                      const SizedBox(height: 8),
                      _buildPieLegend('Absen (1)', Colors.red[500]!),
                    ],
                  ),
                  const SizedBox(width: 16),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // =========== WEEKLY VIEW ===========
  Widget _buildWeeklyView(bool isDark) {
    final random = Random(77);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _buildStatCard('Total Jam', '42.5h', Icons.timer, Colors.indigo, isDark),
              const SizedBox(width: 12),
              _buildStatCard('Rata-rata', '8.5h', Icons.speed, Colors.teal, isDark),
              const SizedBox(width: 12),
              _buildStatCard('Lembur', '2.5h', Icons.more_time, Colors.purple, isDark),
            ],
          ),
          const SizedBox(height: 20),

          _buildChartContainer(
            title: 'Jam Kerja per Hari',
            subtitle: 'Minggu ke-3 Agustus',
            isDark: isDark,
            child: SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: 12,
                  barTouchData: BarTouchData(
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        const days = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];
                        return BarTooltipItem(
                          '${days[group.x]}\n',
                          const TextStyle(color: Colors.white, fontSize: 11),
                          children: [
                            TextSpan(
                              text: '${rod.toY.toStringAsFixed(1)} jam',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                          ],
                        );
                      },
                    ),
                  ),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        interval: 4,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            '${value.toInt()}h',
                            style: TextStyle(fontSize: 10, color: Colors.grey[500]),
                          );
                        },
                      ),
                    ),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          const days = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];
                          if (value.toInt() < days.length) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(
                                days[value.toInt()],
                                style: TextStyle(fontSize: 10, color: Colors.grey[500], fontWeight: FontWeight.w500),
                              ),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                  ),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 4,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: isDark ? Colors.white10 : Colors.grey[200]!,
                      strokeWidth: 1,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: List.generate(7, (i) {
                    final hours = i < 5 ? (7.5 + random.nextDouble() * 2) : (i == 5 ? 4.0 : 0.0);
                    final isOvertime = hours > 9;
                    return BarChartGroupData(
                      x: i,
                      barRods: [
                        BarChartRodData(
                          toY: hours,
                          width: 20,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
                          gradient: LinearGradient(
                            begin: Alignment.bottomCenter,
                            end: Alignment.topCenter,
                            colors: isOvertime
                                ? [Colors.purple[300]!, Colors.purple[600]!]
                                : [Colors.indigo[300]!, Colors.indigo[600]!],
                          ),
                        ),
                      ],
                    );
                  }),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Trend line chart
          _buildChartContainer(
            title: 'Tren Jam Masuk',
            subtitle: 'Target: 08:00',
            isDark: isDark,
            child: SizedBox(
              height: 160,
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
                        getTitlesWidget: (value, meta) {
                          const days = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum'];
                          if (value.toInt() >= 0 && value.toInt() < days.length) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(days[value.toInt()],
                                  style: TextStyle(fontSize: 10, color: Colors.grey[500])),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  minY: 470,
                  maxY: 510,
                  extraLinesData: ExtraLinesData(
                    horizontalLines: [
                      HorizontalLine(
                        y: 480,
                        color: Colors.green.withOpacity(0.5),
                        strokeWidth: 1.5,
                        dashArray: [8, 4],
                        label: HorizontalLineLabel(
                          show: true,
                          alignment: Alignment.topRight,
                          style: TextStyle(fontSize: 9, color: Colors.green[700]),
                          labelResolver: (_) => '08:00',
                        ),
                      ),
                    ],
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: List.generate(5, (i) {
                        return FlSpot(i.toDouble(), 478 + random.nextInt(20).toDouble());
                      }),
                      isCurved: true,
                      curveSmoothness: 0.35,
                      color: Colors.red[400]!,
                      barWidth: 2.5,
                      isStrokeCapRound: true,
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, percent, barData, index) {
                          return FlDotCirclePainter(
                            radius: 4,
                            color: spot.y > 480 ? Colors.orange : Colors.green,
                            strokeWidth: 2,
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
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // =========== MONTHLY VIEW ===========
  Widget _buildMonthlyView(bool isDark) {
    final random = Random(123);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _buildStatCard('Kehadiran', '95%', Icons.trending_up, Colors.green, isDark),
              const SizedBox(width: 12),
              _buildStatCard('Tepat Waktu', '89%', Icons.alarm_on, Colors.blue, isDark),
              const SizedBox(width: 12),
              _buildStatCard('Skor', 'A', Icons.star, Colors.amber, isDark),
            ],
          ),
          const SizedBox(height: 20),

          // Multi-month trend
          _buildChartContainer(
            title: 'Tren Kehadiran 6 Bulan',
            subtitle: 'Persentase kehadiran bulanan',
            isDark: isDark,
            child: SizedBox(
              height: 200,
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
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 35,
                        interval: 10,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            '${value.toInt()}%',
                            style: TextStyle(fontSize: 10, color: Colors.grey[500]),
                          );
                        },
                      ),
                    ),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          const months = ['Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags'];
                          if (value.toInt() >= 0 && value.toInt() < months.length) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(months[value.toInt()],
                                  style: TextStyle(fontSize: 10, color: Colors.grey[500], fontWeight: FontWeight.w500)),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  minY: 70,
                  maxY: 105,
                  lineBarsData: [
                    // Kehadiran line
                    LineChartBarData(
                      spots: [
                        const FlSpot(0, 88),
                        const FlSpot(1, 92),
                        const FlSpot(2, 90),
                        const FlSpot(3, 95),
                        const FlSpot(4, 93),
                        const FlSpot(5, 96),
                      ],
                      isCurved: true,
                      curveSmoothness: 0.35,
                      color: Colors.green[500]!,
                      barWidth: 3,
                      isStrokeCapRound: true,
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
                          radius: 4,
                          color: Colors.green[500]!,
                          strokeWidth: 2,
                          strokeColor: Colors.white,
                        ),
                      ),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.green[400]!.withOpacity(0.3),
                            Colors.green[400]!.withOpacity(0.0),
                          ],
                        ),
                      ),
                    ),
                    // Tepat Waktu line
                    LineChartBarData(
                      spots: [
                        const FlSpot(0, 82),
                        const FlSpot(1, 85),
                        const FlSpot(2, 83),
                        const FlSpot(3, 89),
                        const FlSpot(4, 87),
                        const FlSpot(5, 91),
                      ],
                      isCurved: true,
                      curveSmoothness: 0.35,
                      color: Colors.blue[500]!,
                      barWidth: 2.5,
                      isStrokeCapRound: true,
                      dashArray: [6, 4],
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
                          radius: 3,
                          color: Colors.blue[500]!,
                          strokeWidth: 2,
                          strokeColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (touchedSpots) {
                        return touchedSpots.map((spot) {
                          final label = spot.barIndex == 0 ? 'Hadir' : 'Tepat';
                          return LineTooltipItem(
                            '$label: ${spot.y.toStringAsFixed(0)}%',
                            TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 11,
                            ),
                          );
                        }).toList();
                      },
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildLegendDot('Kehadiran', Colors.green[500]!),
              const SizedBox(width: 20),
              _buildLegendDot('Tepat Waktu', Colors.blue[500]!),
            ],
          ),
          const SizedBox(height: 16),

          // Monthly comparison bars
          _buildChartContainer(
            title: 'Perbandingan Bulanan',
            subtitle: 'Hadir vs Terlambat vs Absen',
            isDark: isDark,
            child: SizedBox(
              height: 180,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: 25,
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 25,
                        interval: 5,
                        getTitlesWidget: (value, meta) =>
                            Text('${value.toInt()}', style: TextStyle(fontSize: 10, color: Colors.grey[500])),
                      ),
                    ),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          const months = ['Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags'];
                          if (value.toInt() < months.length) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(months[value.toInt()],
                                  style: TextStyle(fontSize: 10, color: Colors.grey[500])),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                  ),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 5,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: isDark ? Colors.white10 : Colors.grey[200]!,
                      strokeWidth: 1,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: List.generate(6, (i) {
                    return BarChartGroupData(
                      x: i,
                      barsSpace: 3,
                      barRods: [
                        BarChartRodData(
                          toY: 18 + random.nextInt(4).toDouble(),
                          width: 10,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(3)),
                          color: Colors.green[500]!,
                        ),
                        BarChartRodData(
                          toY: random.nextInt(4).toDouble() + 1,
                          width: 10,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(3)),
                          color: Colors.orange[400]!,
                        ),
                        BarChartRodData(
                          toY: random.nextInt(2).toDouble() + 1,
                          width: 10,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(3)),
                          color: Colors.red[400]!,
                        ),
                      ],
                    );
                  }),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildLegendDot('Hadir', Colors.green[500]!),
              const SizedBox(width: 16),
              _buildLegendDot('Terlambat', Colors.orange[400]!),
              const SizedBox(width: 16),
              _buildLegendDot('Absen', Colors.red[400]!),
            ],
          ),
        ],
      ),
    );
  }

  // =========== HELPER WIDGETS ===========
  Widget _buildStatCard(String label, String value, IconData icon, MaterialColor color, bool isDark) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
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
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isDark ? color.withOpacity(0.15) : color[50],
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color[600], size: 18),
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: isDark ? Colors.white : Colors.black87,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(fontSize: 9, color: Colors.grey[500], fontWeight: FontWeight.w500),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChartContainer({
    required String title,
    required String subtitle,
    required bool isDark,
    required Widget child,
  }) {
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
              Text(title, style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: isDark ? Colors.white : Colors.black87,
              )),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isDark ? Colors.grey[800] : Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(subtitle, style: TextStyle(fontSize: 10, color: Colors.grey[500])),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _buildPieLegend(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 12, height: 12,
          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3)),
        ),
        const SizedBox(width: 8),
        Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
      ],
    );
  }

  Widget _buildLegendDot(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 10, height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(label, style: TextStyle(fontSize: 10, color: Colors.grey[500])),
      ],
    );
  }
}
