import 'package:flutter/material.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'course1_screen.dart';  
import 'course2_screen.dart';

void main() {
  runApp(LanguageLearningApp());
}

class LanguageLearningApp extends StatefulWidget {
  @override
  _LanguageLearningAppState createState() => _LanguageLearningAppState();
}

class _LanguageLearningAppState extends State<LanguageLearningApp> {
  late WebSocketChannel _channel;

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
  }

  void _connectWebSocket() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://your_server_address:8000/ws'),
    );
  }

  @override
  void dispose() {
    _channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Language Learning App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        textTheme: TextTheme(
          bodyLarge: TextStyle(fontFamily: 'Comfortaa'),
          bodyMedium: TextStyle(fontFamily: 'Comfortaa'),
        ),
      ),
      home: HomePage(channel: _channel),
    );
  }
}

class HomePage extends StatelessWidget {
  final WebSocketChannel channel;

  HomePage({required this.channel});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF003B46),
      body: StreamBuilder(
        stream: channel.stream,
        builder: (context, snapshot) {
          // if (snapshot.hasError) {
          //   return Center(child: Text('Error: ${snapshot.error}'));
          // }
          // if (snapshot.connectionState == ConnectionState.waiting) {
          //   return Center(child: CircularProgressIndicator());
          // }
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                SpinKitWave(
                  color: Color(0xFFC0DEE5),
                  size: 100.0,
                ),
                SizedBox(height: 40),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    'Welcome to Lang!',
                    style: TextStyle(
                        fontFamily: 'Comfortaa',
                        fontSize: 40,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFC0DEE5)),
                    textAlign: TextAlign.center,
                  ),
                ),
                SizedBox(height: 30),
                RoundedButton(
                  text: 'Introduction and Greetings',
                  color: Color(0xFF07575B),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => Course1Screen(channel: channel)),
                    );
                  },
                ),
                SizedBox(height: 20),
                RoundedButton(
                  text: 'Basic Conversation',
                  color: Color(0xFF07575B),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => Course2Screen(channel: channel)),
                    );
                  },
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class RoundedButton extends StatelessWidget {
  final String text;
  final Color color;
  final VoidCallback onPressed;

  RoundedButton({required this.text, required this.color, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(30.0),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(30.0),
        child: Container(
          padding: EdgeInsets.symmetric(vertical: 15.0, horizontal: 30.0),
          child: Text(
            text,
            style: TextStyle(
              fontFamily: 'Comfortaa',
              fontSize: 20.0,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}