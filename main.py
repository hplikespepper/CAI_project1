from datetime import datetime
from google.cloud import speech, texttospeech_v1

from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory, flash 
from werkzeug.utils import secure_filename

import os


app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('tts', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
            print(filename)
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    # 获取 uploads 和 tts 目录中的文件
    upload_files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    tts_files = [f for f in os.listdir('tts') if f.endswith('.wav')]

    # 排序文件列表（按时间倒序）
    upload_files.sort(reverse=True)
    tts_files.sort(reverse=True)

    return render_template('index.html', upload_files=upload_files, tts_files=tts_files)



# @app.route('/') # yuanban
# def index():
#     files = get_files()
#     return render_template('index.html', files=files)

# @app.route('/audio_files')  # for text to speech
# def index():
#     upload_folder = 'tts'
#     files = [f for f in os.listdir(upload_folder) if f.endswith('.wav')]
#     files.sort(reverse=True)  # 按时间倒序排列
#     return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        # filename = secure_filename(file.filename)
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        #
        #
        # Modify this block to call the speech to text API
        # Save transcript to same filename but .txt
        #
        #
        # Call the speech-to-text API
        client = speech.SpeechClient()
        
        # Load audio data
        with open(file_path, 'rb') as f:
            data = f.read()
        
        audio = speech.RecognitionAudio(content=data)
        config=speech.RecognitionConfig(
        # encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        # sample_rate_hertz=24000,
        language_code="en-US",
        model="latest_long",
        # odel = "default",
        audio_channel_count=1,
        enable_word_confidence=True,
        enable_word_time_offsets=True,
        )
        
        # Perform speech recognition
        operation = client.long_running_recognize(config=config, audio=audio)
        # operation = client.recognize(config=config, audio=audio)
        
        response=operation.result(timeout=90)

        txt = ''
        for result in response.results:
            txt = txt + result.alternatives[0].transcript + '\n'
            print(f'Transcript: {txt}')
        
        # Save the transcript to a .txt file
        transcript_filename = filename + '.txt'
        transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
        with open(transcript_path, "w") as transcript_file:
            transcript_file.write(txt)
        


    return redirect('/') #success

@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)

    
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    print(text)
    #
    #
    # Modify this block to call the stext to speech API
    # Save the output as a audio file in the 'tts' directory 
    # Display the audio files at the bottom and allow the user to listen to them
    #
    client = texttospeech_v1.TextToSpeechClient()

    input = texttospeech_v1.SynthesisInput()
    # if ssml:
    #   input.ssml = ssml
    # else:
    input.text = text

    voice = texttospeech_v1.VoiceSelectionParams()
    voice.language_code = "en-UK"

    audio_config = texttospeech_v1.AudioConfig()
    audio_config.audio_encoding = "LINEAR16"

    request_set = texttospeech_v1.SynthesizeSpeechRequest(
        input=input,
        voice=voice,
        audio_config=audio_config,
    )

    response = client.synthesize_speech(request=request_set)

    # Generate a unique filename for the audio file
    filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    output_dir = os.path.join('tts')
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
    file_path = os.path.join(output_dir, filename)

    # Save the audio content to a file
    with open(file_path, "wb") as audio_file:
        audio_file.write(response.audio_content)

    print(f"Audio file saved at: {file_path}")

    return redirect('/') #success
    # return redirect('/audio_files')




@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tts/<filename>')
def serve_audio(filename):
    return send_from_directory('tts', filename)

if __name__ == '__main__':
    app.run(debug=True)