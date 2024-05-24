import 'package:flutter/material.dart';

class Course2Screen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Basic Conversational Phrases (Course 2)'),
      ),
      body: ListView(
        padding: EdgeInsets.all(16.0),
        children: <Widget>[
          ListTile(
            title: Text('How are you? - ¿Cómo estás?'),
          ),
          ListTile(
            title: Text('What is your name? - ¿Cuál es tu nombre?'),
          ),
          ListTile(
            title: Text('Where are you from? - ¿De dónde eres?'),
          ),
        ],
      ),
    );
  }
}
