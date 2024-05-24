import 'package:flutter/material.dart';

class Course1Screen extends StatelessWidget {
  const Course1Screen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Basic Greetings (Course 1)'),
      ),
      body: ListView(
        padding: EdgeInsets.all(16.0),
        children: <Widget>[
          ListTile(
            title: Text('Hello! - ¡Hola!'),
          ),
          ListTile(
            title: Text('Good Morning! - ¡Buenos días!'),
          ),
          ListTile(
            title: Text('Good Evening! - ¡Buenas noches!'),
          ),
        ],
      ),
    );
  }
}
