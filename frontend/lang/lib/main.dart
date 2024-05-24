import 'package:flutter/material.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'course1_screen.dart';
import 'course2_screen.dart';

void main() {
  runApp(LanguageLearningApp());
}

class LanguageLearningApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Language Learning App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        textTheme: TextTheme(
          bodyText1: TextStyle(fontFamily: 'Comfortaa'),
          bodyText2: TextStyle(fontFamily: 'Comfortaa'),
        ),
      ),
      home: HomePage(),
    );
  }
}

// 003B46
// 07575B
// 61A4AD
// C0DEE5

class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF003B46),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            // Animation similar to voice agents
            SpinKitWave(
              color: Color(0xFFC0DEE5),
              size: 100.0,
            ),
            SizedBox(height: 40),
            // Text transcription
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
                  MaterialPageRoute(builder: (context) => Course1Screen()),
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
                  MaterialPageRoute(builder: (context) => Course2Screen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class RoundedButton extends StatelessWidget {
  final String text;
  final Color color;
  final VoidCallback onPressed;

  RoundedButton(
      {required this.text, required this.color, required this.onPressed});

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
