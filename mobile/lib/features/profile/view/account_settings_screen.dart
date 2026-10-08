import 'package:flutter/material.dart';
import 'profile_sub_screens.dart';
import 'admin_settings_screen.dart';

class AccountSettingsScreen extends StatelessWidget {
  const AccountSettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pengaturan Akun'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildMenu(
            context,
            icon: Icons.badge,
            title: 'Data Karyawan',
            subtitle: 'Lengkapi biodata diri dan identitas',
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const EmployeeDataScreen()));
            },
          ),
          _buildMenu(
            context,
            icon: Icons.account_balance,
            title: 'Info Rekening',
            subtitle: 'Pengaturan nomor rekening untuk penggajian',
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const BankAccountScreen()));
            },
          ),
          _buildMenu(
            context,
            icon: Icons.contact_emergency,
            title: 'Kontak Darurat',
            subtitle: 'Kontak yang bisa dihubungi saat darurat',
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const EmergencyContactScreen()));
            },
          ),
          const Divider(),
          _buildMenu(
            context,
            icon: Icons.admin_panel_settings,
            title: 'Pengaturan Perusahaan (Admin)',
            subtitle: 'Atur radius, jam masuk, dan jam keluar',
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminSettingsScreen()));
            },
          ),
        ],
      ),
    );
  }

  Widget _buildMenu(BuildContext context, {required IconData icon, required String title, required String subtitle, required VoidCallback onTap}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey[200]!),
      ),
      color: isDark ? const Color(0xFF2B303B) : Colors.white,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: Colors.red[50],
          child: Icon(icon, color: Colors.red[700]),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
