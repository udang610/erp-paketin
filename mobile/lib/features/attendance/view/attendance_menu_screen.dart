import 'package:flutter/material.dart';
import 'attendance_menu_tab.dart';

class AttendanceMenuScreen extends StatelessWidget {
  const AttendanceMenuScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Menu Kehadiran'),
        elevation: 0,
      ),
      body: const AttendanceMenuTab(),
    );
  }
}
