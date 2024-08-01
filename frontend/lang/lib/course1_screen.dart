import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:convert';
import 'dart:async';
import 'dart:io';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:record/record.dart';

class Course1Screen extends StatefulWidget {
  final WebSocketChannel channel;

  const Course1Screen({Key? key, required this.channel}) : super(key: key);

  @override
  _Course1ScreenState createState() => _Course1ScreenState();
}

class _Course1ScreenState extends State<Course1Screen> {
  bool isRecording = false;
  late Record _recorder;
  String transcription = '';
  late WebSocketChannel _channel;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _recorder = Record();
    _initRecorder();
    _connectWebSocket();
  }

  Future<void> _initRecorder() async {
    final status = await Permission.microphone.request();
    if (status != PermissionStatus.granted) {
      throw Exception('Microphone permission not granted');
    }
  }

  void _connectWebSocket() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://your_server_address:8000/ws'),
    );
    _channel.stream.listen((message) {
      final data = jsonDecode(message);
      setState(() {
        transcription = data['transcription'];
      });
    });
  }

  Future<void> _startRecording() async {
    if (await _recorder.hasPermission()) {
      await _recorder.start(
        encoder: AudioEncoder.pcm16bit,
        samplingRate: 16000,
        numChannels: 1,
      );

      _streamAudioData();
    }
  }

  void _streamAudioData() {
    _timer = Timer.periodic(Duration(milliseconds: 100), (timer) async {
      if (!isRecording) {
        timer.cancel();
        return;
      }

      try {
        final path = await _recorder.stop();
        if (path != null) {
          final bytes = await File(path).readAsBytes();
          final base64Audio = base64Encode(bytes);
          _channel.sink.add(jsonEncode({'audio': base64Audio}));
        }
        await _recorder.start(
          encoder: AudioEncoder.pcm16bit,
          samplingRate: 16000,
          numChannels: 1,
        );
      } catch (e) {
        print('Error streaming audio: $e');
      }
    });
  }

  Future<void> _stopRecording() async {
    _timer?.cancel();
    await _recorder.stop();
    _channel.sink.add(jsonEncode({'audio': 'END'}));
  }

  @override
  void dispose() {
    _timer?.cancel();
    _recorder.dispose();
    _channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF003B46),
      appBar: AppBar(
        title: Text('Basic Greetings', style: TextStyle(fontFamily: 'Comfortaa')),
        backgroundColor: Color(0xFF07575B),
        elevation: 0,
      ),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Expanded(
              child: Center(
                child: Text(
                  'Practice Your Pronunciation',
                  style: TextStyle(
                    fontFamily: 'Comfortaa',
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFC0DEE5),
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
            Expanded(
              flex: 2,
              child: Center(
                child: RecordButton(
                  isRecording: isRecording,
                  onTap: () {
                    setState(() {
                      isRecording = !isRecording;
                    });
                    if (isRecording) {
                      _stopRecording();
                    } else {
                      _startRecording();
                    }
                  },
                ),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: LiveTranscription(transcription: transcription),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class RecordButton extends StatelessWidget {
  final bool isRecording;
  final VoidCallback onTap;

  RecordButton({required this.isRecording, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isRecording ? Colors.red : Color(0xFF61A4AD),
            boxShadow: [
              BoxShadow(
                color: Colors.black26,
                blurRadius: 10,
                offset: Offset(0, 5),
              ),
            ],
          ),
          child: Center(
            child: Icon(
              isRecording ? Icons.stop : Icons.mic,
              color: Colors.white,
              size: 60,
            ),
          ),
        ),
      ),
    );
  }
}

class LiveTranscription extends StatelessWidget {
  final String transcription;

  LiveTranscription({required this.transcription});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFF07575B),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        transcription.isEmpty ? 'Start speaking...' : transcription,
        style: TextStyle(
          fontFamily: 'Comfortaa',
          fontSize: 18,
          color: Color(0xFFC0DEE5),
        ),
        textAlign: TextAlign.center,
      ),
    );
  }
}