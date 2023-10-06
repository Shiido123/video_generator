from moviepy.editor import *
import openai
import requests
import os
import json
from datetime import datetime

with open('config.json') as config_file:
    config_content = config_file.read()
configjson = json.loads(config_content)

openai.api_key = configjson['openai']
CHUNK_SIZE = 1024
# configjson.elevenlabs
url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": configjson["elevenlabs"]
}

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": "Tu es un célèbre écrivain d'histoire. Tu dois créer une histoire intéressante, avec une morale à la fin."},
              {
        "role": "user",
        "content": "Bonjour, je voudrais avoir une anecdote historique illustrée d'environ 1 minute. Pour cela, j'ai besoin d'un tableau d'objets Python avec pour chaque phrase un nouvel objet comprenant la phrase en question et un prompt pour générer l'image, il faut que le prompt soit précis. Le prompt ne doit pas faire référence aux autres parties du text/prompts, comme ceci : \"un chateau blanc dans un ciel bleu avec quelques nuages\" et non pas \"Le chateau blanc dans un ciel bleu avec quelques nuages\" . Peux-tu me le faire en français s'il te plaît ? Assure toi que l'histoire ait un sens, qu'elle ait une morale et ne se finnisse pas brusquement."
    },
        {
        "role": "assistant",
        "content": "[{\"phrase\": \"Au cœur de la France, s'élevait le majestueux château de Versailles.\", \"prompt\": \"Le grand château de Versailles avec ses jardins luxuriants, ses fontaines et son architecture splendide.\"}, {\"phrase\": \"Au XVIIème siècle, c'était la résidence de plusieurs monarques, dont Louis XIV.\", \"prompt\": \"Un roi en tenue royale marchant dans les couloirs de Versailles, entouré de courtisans.\"}, {\"phrase\": \"Cependant, ce château n'était pas juste une demeure, il recelait de nombreux secrets.\", \"prompt\": \"Des passages secrets et des salles cachées disséminés dans le château.\"}, {\"phrase\": \"Parmi les résidents du château, il y avait une femme influente, Madame de Maintenon, l'épouse secrète de Louis XIV.\", \"prompt\": \"Une dame élégante en robe du XVIIème siècle, portant une tiare.\"}, {\"phrase\": \"Elle était connue pour son intelligence et son influence sur le roi.\", \"prompt\": \"Madame de Maintenon chuchotant à l'oreille du roi Louis XIV dans une salle du trône.\"}, {\"phrase\": \"Un jour, dans une pièce secrète, elle rencontra des intellectuels et des artistes pour discuter des affaires du royaume.\", \"prompt\": \"Madame de Maintenon entourée d'intellectuels, discutant dans une pièce cachée du château.\"}, {\"phrase\": \"Grâce à ces rencontres, elle a joué un rôle clé dans la promotion des arts et des sciences à Versailles.\", \"prompt\": \"Des artistes et des scientifiques présentant leurs œuvres et découvertes à la cour.\"}, {\"phrase\": \"Son influence montre que, même à une époque où les femmes étaient souvent reléguées au second plan, elles pouvaient jouer un rôle déterminant dans la direction d'un pays.\", \"prompt\": \"Madame de Maintenon debout fièrement, avec le château de Versailles en arrière-plan.\"}]"
    },

        {
        "role": "user",
        "content": "Peux-tu m'en générer un nouveau similaire à celui-ci ?"
    }

    ],
)

msgrep = response.choices[0].message.content
tableau_str = msgrep[msgrep.find("["):msgrep.find("]") + 1]
histoire = json.loads(tableau_str)

if histoire:
    i = 0

    folder_name = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(folder_name, exist_ok=True)

    for obj in histoire:
        phrase = obj["phrase"]
        prompt = obj["prompt"]
        print("Phrase :", phrase)
        print("Prompt :", prompt)
        try:
            img = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            previous_image_url = img
        except Exception as e:
            print("erreur dans la création de l'image:"+str(e))
            if previous_image_url:
                img = previous_image_url
        print(f"image n°{i} générée")
        print("---------")

        data = {
            "text": phrase,
            "model_id": "eleven_multilingual_v1",
            "language": "french",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        reponse = requests.post(url, json=data, headers=headers)

        with open(os.path.join(folder_name, "audio" + str(i) + ".mp3"), "wb") as f:  # chemin modifié
            for chunk in reponse.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        audio_file = os.path.join(folder_name, "audio" + str(i) + ".mp3")
        image_file = img.data[0].url
        # Remplacez par le nom de fichier de sortie souhaité
        output_file = os.path.join(folder_name, "output" + str(i) + ".mp4")

        audio_clip = AudioFileClip(audio_file)
        image_clip = ImageClip(image_file)

        video = image_clip.set_audio(audio_clip)
        video.duration = audio_clip.duration
        video.fps = 15

        video.write_videofile("output" + str(i) + ".mp4")

        i = i + 1
        print(i)

    video_clips = []

    for i in range(0, len(histoire)):
        try:
            file_name = "output" + str(i) + ".mp4"
            video_clip = VideoFileClip(file_name)
            video_clips.append(video_clip)
            print(video_clips)

            final_clip = concatenate_videoclips(video_clips)

            final_output_file = os.path.join(folder_name, "output_final.mp4")
            final_clip.write_videofile(
                final_output_file, codec="libx264", audio_codec="aac")
        except Exception as e:
            print("erreur : " + e)

    for i in range(0, len(histoire)):
        file_name = os.path.join(
            folder_name, "output" + str(i) + ".mp4")  # chemin modifié
        if os.path.exists(file_name):
            os.remove(file_name)
            print(file_name + " bien supprimé")

    print("video terminée avec succes")
else:
    print("problème : histoire non valide, essayez de relancer le proggrame")
