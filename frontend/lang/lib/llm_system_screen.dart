import 'package:flutter/material.dart';

class LLMSystemScreen extends StatelessWidget {
  final int courseNumber;

  const LLMSystemScreen({required this.courseNumber});

  @override
  Widget build(BuildContext context) {
    List<String> generatedContent = _generateContent(courseNumber);

    return Scaffold(
      appBar: AppBar(
        title: Text('Course $courseNumber with LLM'),
      ),
      body: ListView.builder(
        padding: EdgeInsets.all(16.0),
        itemCount: generatedContent.length,
        itemBuilder: (context, index) {
          return ListTile(
            title: Text(generatedContent[index]),
          );
        },
      ),
    );
  }

  List<String> _generateContent(int courseNumber) {
    if (courseNumber == 1) {
      return [
        'Hello! - ¡Hola! (LLM)',
        'Good Morning! - ¡Buenos días! (LLM)',
        'Good Evening! - ¡Buenas noches! (LLM)'
      ];
    } else {
      return [
        'How are you? - ¿Cómo estás? (LLM)',
        'What is your name? - ¿Cuál es tu nombre? (LLM)',
        'Where are you from? - ¿De dónde eres? (LLM)'
      ];
    }
  }
}
