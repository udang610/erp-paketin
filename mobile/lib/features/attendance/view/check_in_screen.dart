import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../auth/provider/auth_provider.dart';
import '../../home/provider/timer_provider.dart';

class CheckInScreen extends ConsumerStatefulWidget {
  const CheckInScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<CheckInScreen> createState() => _CheckInScreenState();
}

class _CheckInScreenState extends ConsumerState<CheckInScreen> {
  bool _isLocating = true;
  bool _isSubmitting = false;
  String _locationStatus = "Mendapatkan lokasi...";
  
  CameraController? _controller;
  List<CameraDescription>? _cameras;

  // Paketin Cargo office coordinates
  static const double _officeLat = -6.310984;
  static const double _officeLng = 106.926989;

  @override
  void initState() {
    super.initState();
    _initCamera();
    // Simulate getting GPS coordinates (in production, use geolocator)
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isLocating = false;
          _locationStatus = "Lokasi: Kantor Paketin Cargo\nJl. Arteri Jorr Jatiwarna No.55, Jatimelati, Kec. Pd. Melati, Kota Bks";
        });
      }
    });
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras != null && _cameras!.isNotEmpty) {
        CameraDescription selectedCamera = _cameras!.firstWhere(
          (c) => c.lensDirection == CameraLensDirection.front,
          orElse: () => _cameras![0],
        );
        _controller = CameraController(selectedCamera, ResolutionPreset.medium);
        await _controller!.initialize();
        if (mounted) setState(() {});
      }
    } catch (e) {
      debugPrint("Error initializing camera: $e");
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _submitAttendance({String? customNotes}) async {
    if (_isSubmitting) return;
    setState(() => _isSubmitting = true);

    try {
      final apiClient = ref.read(apiClientProvider);
      final now = DateTime.now();
      
      XFile? imageFile;
      if (_controller != null && _controller!.value.isInitialized) {
        imageFile = await _controller!.takePicture();
      }

      final formDataMap = {
        'event_type': 'CHECK_IN',
        'device_timestamp': now.toIso8601String(),
        'latitude': _officeLat.toString(),
        'longitude': _officeLng.toString(),
        'gps_accuracy': 15.0,
        'is_mock_location': false,
        'notes': customNotes ?? '',
      };

      if (imageFile != null) {
        final bytes = await imageFile.readAsBytes();
        formDataMap['photo'] = MultipartFile.fromBytes(
          bytes,
          filename: 'attendance_${now.millisecondsSinceEpoch}.jpg',
        );
      }

      final formData = FormData.fromMap(formDataMap);

      final String fullUrl = 'http://127.0.0.1:8000/hr/attendance/api/events/';
      await apiClient.dio.post(
        fullUrl,
        data: formData,
      );

      if (mounted) {
        ref.read(checkInTimeProvider.notifier).state = now;
        _showSuccessDialog(now);
      }
    } on DioException catch (e) {
      if (mounted) {
        final data = e.response?.data;
        if (data != null && data['error_code'] == 'REQUIRES_REASON') {
          // Show reason dialog instead of snackbar
          setState(() => _isSubmitting = false);
          _showReasonDialog(data['detail'] ?? 'Silakan masukkan alasan:');
          return;
        }

        String errMsg = '';
        if (data is Map) {
          errMsg = data['detail'] ?? data['non_field_errors']?[0] ?? data.toString();
        } else {
          errMsg = e.message ?? 'Unknown error';
        }
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal submit absensi: $errMsg'),
            backgroundColor: Colors.red[700],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal submit absensi: ${e.toString()}'),
            backgroundColor: Colors.red[700],
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        title: const Text('Verifikasi Wajah', style: TextStyle(color: Colors.white)),
      ),
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          // Live Camera Preview or Loading Placeholder
          (_controller != null && _controller!.value.isInitialized)
              ? SizedBox(
                  width: double.infinity,
                  height: double.infinity,
                  child: CameraPreview(_controller!),
                )
              : Container(
                  color: Colors.grey[900],
                  width: double.infinity,
                  height: double.infinity,
                  child: const Center(
                    child: CircularProgressIndicator(color: Colors.white54),
                  ),
                ),
          
          // Bottom Status & Camera Shutter Action
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.only(top: 12, left: 16, right: 16, bottom: 16),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 2.0),
                        child: Icon(
                          Icons.location_on, 
                          color: _isLocating ? Colors.orange : Colors.green,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _locationStatus,
                          style: TextStyle(
                            color: Colors.grey[800],
                            fontWeight: FontWeight.w500,
                            fontSize: 12,
                            height: 1.3,
                          ),
                        ),
                      ),
                      if (_isLocating)
                        const SizedBox(
                          width: 12,
                          height: 12,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Camera Shutter Circle Button
                  GestureDetector(
                    onTap: (_isLocating || _isSubmitting) ? null : _submitAttendance,
                    child: Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: (_isLocating || _isSubmitting) ? Colors.grey[400]! : Colors.red[700]!,
                          width: 2,
                        ),
                      ),
                      child: Center(
                        child: _isSubmitting
                            ? SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.5,
                                  color: Colors.red[700],
                                ),
                              )
                            : Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  color: (_isLocating || _isSubmitting) ? Colors.grey[300] : Colors.red[700],
                                  shape: BoxShape.circle,
                                ),
                              ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _isSubmitting ? 'Mengirim...' : 'Ambil Foto',
                    style: TextStyle(color: Colors.grey[600], fontWeight: FontWeight.bold, fontSize: 12),
                  )
                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  void _showSuccessDialog(DateTime time) {
    final timeStr = DateFormat('HH:mm').format(time);
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle, color: Colors.green, size: 64),
            const SizedBox(height: 16),
            const Text(
              'Absen Berhasil!',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              'Waktu: $timeStr WIB\nLokasi: Kantor Paketin Cargo\nStatus: Hadir',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600], height: 1.4),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pop(); // close dialog
                  Navigator.of(context).pop(); // go back to home
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red[700],
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text(
                  'KEMBALI KE DASHBOARD',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
  void _showReasonDialog(String titleMsg) {
    final reasonController = TextEditingController();
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Butuh Alasan', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(titleMsg, style: TextStyle(color: Colors.grey[700], fontSize: 14)),
              const SizedBox(height: 16),
              TextField(
                controller: reasonController,
                maxLines: 3,
                decoration: InputDecoration(
                  hintText: 'Tulis alasan Anda di sini...',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Batal', style: TextStyle(color: Colors.grey[600])),
            ),
            ElevatedButton(
              onPressed: () {
                final reason = reasonController.text.trim();
                if (reason.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Alasan tidak boleh kosong.')));
                  return;
                }
                Navigator.pop(context);
                _submitAttendance(customNotes: reason);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red[700],
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text('Kirim Absen'),
            )
          ],
        );
      }
    );
  }
}
