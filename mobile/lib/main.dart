import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'features/auth/provider/auth_provider.dart';
import 'features/auth/view/login_screen.dart';
import 'features/auth/view/splash_screen.dart';
import 'features/home/view/home_screen.dart';
import 'core/providers/theme_provider.dart';

void main() {
  runApp(
    const ProviderScope(
      child: HRPaketinApp(),
    ),
  );
}

class HRPaketinApp extends ConsumerStatefulWidget {
  const HRPaketinApp({Key? key}) : super(key: key);

  @override
  ConsumerState<HRPaketinApp> createState() => _HRPaketinAppState();
}

class _HRPaketinAppState extends ConsumerState<HRPaketinApp> {
  bool _showSplash = true;

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp(
      title: 'Paketin HR',
      debugShowCheckedModeBanner: false,
      themeMode: themeMode,
      theme: ThemeData(
        brightness: Brightness.light,
        primarySwatch: Colors.red,
        primaryColor: Colors.red[700],
        textTheme: GoogleFonts.interTextTheme(ThemeData.light().textTheme),
        visualDensity: VisualDensity.adaptivePlatformDensity,
        scaffoldBackgroundColor: Colors.grey[50],
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.red[700],
          foregroundColor: Colors.white,
          elevation: 0,
        ),
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.red,
        primaryColor: Colors.red[700],
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        visualDensity: VisualDensity.adaptivePlatformDensity,
        scaffoldBackgroundColor: const Color(0xFF121212),
        cardColor: const Color(0xFF1E1E1E),
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.red[700],
          foregroundColor: Colors.white,
          elevation: 0,
        ),
      ),
      home: _showSplash
          ? SplashScreen(onFinished: () {
              setState(() => _showSplash = false);
            })
          : authState.isAuthenticated
              ? const HomeScreen()
              : const LoginScreen(),
    );
  }
}
