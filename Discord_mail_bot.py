#https://security.google.com/settings/security/apppasswords
#https://discordapp.com/developers/applications

#BOT
import discord
from discord.ext import tasks, commands
import asyncio
import random
import time
from datetime import datetime

#Mail
import imaplib
import email
from email.utils import parsedate_tz, mktime_tz, formatdate
from email.header import Header, decode_header, make_header
from email import policy
import re
import os

#CREDENTIAL
mail_login = '@gmail.com'                                      #Adresse mail (tester avec Gmail)
mail_pswd = ''                                              #Mot de passe IMAP
mail_label = ''                                                          #Libellé
IMAP_SERVER = 'imap.gmail.com'                                            #Serveur IMAP
ID_CHANNEl =                                              #ID du channel Discord
TOKEN = ''       #Token d'application Discord
PREFIX = '$'

#Temps à attendre entre chaque affichage d'ancien mail
time_wait = 1
#Limiter le nombre d'ancien mail à afficher (pour éviter de spam)
limite_mail = 12

description = '''Liste de commandes avec leurs explications :'''
bot = commands.Bot(command_prefix=PREFIX, description=description)


#Valeurs par défaut si vide
de_mail = 'de_mail VIDE'
date_mail = 'date_mail VIDE'
objet_mail = 'objet_mail VIDE'
contenu_mail = 'contenu_mail VIDE'
there_is_attachment = False
attachments = []
svdir = 'filename/'     #Repertoire crée pour stocker les pièces jointes

#Inistialisation du bot
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    pourbot = bot.get_channel(ID_CHANNEl)
    #await pourbot.send("**Bot initialisé**")
    

async def check_new_mail():
    while True:
        nombre_mail_total = 0
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(mail_login, mail_pswd)
        mail.select(mail_label)
        type, data = mail.search(None, '(UNSEEN)')
        mail_ids = data[0]
        id_list = mail_ids.split()
        if len(id_list) > nombre_mail_total:
            print('New Mail Found...\n')
            await bot.wait_until_ready()
            channel = bot.get_channel(ID_CHANNEl)
            await send_all_data(channel)
                       

            for i in range(int(id_list[-1]), int(id_list[0]) -1, -1):
                data = mail.fetch(str(i), '(RFC822)')

            nombre_mail_total = len(id_list)
        mail.close()
        mail.logout()
        await asyncio.sleep(30)


def recup_mail(id_mail):
    global de_mail
    global date_mail
    global objet_mail
    global contenu_mail
    global there_is_attachment
    global attachments

    #Connection
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(mail_login, mail_pswd)
    mail.select(mail_label)

    #Récupération données
    result, data = mail.search(None, "ALL")
    ids = data[0] # data is a list.
    id_list = ids.split() # ids is a space separated string
    latest_email_id = id_list[id_mail] # get the latest

    result, data = mail.fetch(latest_email_id, "(RFC822)") # fetch the email body (RFC822) for the given ID
    
    raw_email = data[0][1] # here's the body, which is raw text of the whole email
    # including headers and alternate payloads

    #Convertir email pur en objet EmailMessage
    email_message = email.message_from_bytes(raw_email,policy=email.policy.default)
    #print(str(email_message))
    #Récupérer tout types d'email (avec attachment, multipart)

    for part in email_message.walk():
        if part.is_attachment():
            there_is_attachment = True
            attachment_type = part.get_content_type()
            filename = part.get_filename()
            data = part.get_payload()
            attachments.append((attachment_type, filename))

            if filename is not None:
                sv_path = os.path.join(svdir, filename)
                if not os.path.isfile(sv_path):
                    print(sv_path)
                    fp = open(sv_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
        elif part.get_content_type() == "text/plain":
            content = part.get_content()
            content = re.sub(r'^\s*>.*\n', '', content, flags=re.MULTILINE)
            contenu_mail = str(content)
        
    de_mail = str('Email de '+email.utils.parseaddr(email_message['From'])[0])
    print(de_mail)

    Objet_mail_non_traiter = email_message['Subject']
    objet_mail = str(make_header(decode_header(Objet_mail_non_traiter)))
    print('Objet : '+objet_mail) #Afficher objet du mail

    email_date=email_message['Date']
    tt = parsedate_tz(email_date)
    date_sans_parenthese=str(tt).split("(")
    date_sans_parenthese2=str(date_sans_parenthese[1]).split(")")
    date_split_final=date_sans_parenthese2[0].split(",")
    date_annee=date_split_final[0]
    date_mois=date_split_final[1]
    date_jour=date_split_final[2]
    date_heure=date_split_final[3]
    date_minute=date_split_final[4]
    date_seconde=date_split_final[5]
    date_mail=str('Date du mail : Le '+date_jour+' -'+date_mois+' - '+ date_annee+',  À '+date_heure+' h'+date_minute+' :'+date_seconde)
    print(date_mail)

    if there_is_attachment == True:
        for a in range (len(attachments)):
            attachments[a] = str(attachments[a]).replace('(', '')
            attachments[a] = str(attachments[a]).replace(')', '')
            attachments[a] = str(attachments[a]).replace("'", '')
            attachments[a] = str(attachments[a]).replace(' ', '', 1)
            attachments[a] = str(attachments[a]).split(',')
            print(str(attachments[a][1]))

    mail.close()
    mail.logout()


async def send_all_data(channel):
    global de_mail
    global date_mail
    global objet_mail
    global contenu_mail
    global there_is_attachment
    global attachments

    paginator = commands.Paginator()

    recup_mail(-1)  # Récupérer le dernier mail
    time.sleep(time_wait)
    embed = discord.Embed(color=0x00ff00)
    embed.add_field(name="De", value=de_mail, inline=False)
    embed.add_field(name="Date", value=date_mail, inline=False)
    embed.add_field(name="Objet", value=objet_mail, inline=False)

    for line in contenu_mail.split('\n'):
        paginator.add_line(line)

    if there_is_attachment == True:
        embed.add_field(name="Attachement", value="Nombre : " + str(len(attachments)), inline=False)
        await channel.send(embed=embed)

        for page in paginator.pages:
            await channel.send(page)

        for x in range(len(attachments)):
            print(attachments[x][1])
            attachments[x][1] = attachments[x][1].replace(']', '')
            await channel.send(file=discord.File('filename/' + attachments[x][1]))
        there_is_attachment = False
        attachments = []
        paginator.clear()
    else:
        await channel.send(embed=embed)
        for page in paginator.pages:
            await channel.send(page)
        paginator.clear()



@bot.command()
async def ancien(ctx, times: int):
    """Afficher les x anciens mails (limité pour éviter le spam)."""
    global de_mail
    global date_mail
    global objet_mail
    global contenu_mail
    global there_is_attachment
    global attachments

    if times >= limite_mail:
        await ctx.send("Désoler, le nombre entré est trop grand")
    elif times <= 12:
        paginator = commands.Paginator()

        for nb in range(-1, -times - 1, -1):
            recup_mail(nb)
            time.sleep(time_wait)
            embed = discord.Embed(title="Mail numéro " + str(nb), color=0x00ff00)
            embed.add_field(name="De", value=de_mail, inline=False)
            embed.add_field(name="Date", value=date_mail, inline=False)
            embed.add_field(name="Objet", value=objet_mail, inline=False)

            for line in contenu_mail.split('\n'):
                paginator.add_line(line)

            if there_is_attachment == True:
                embed.add_field(name="Attachement", value="Nombre : " + str(len(attachments)), inline=False)
                await ctx.send(embed=embed)

                for page in paginator.pages:
                    await ctx.send(page)

                for x in range(len(attachments)):
                    print(attachments[x][1])
                    attachments[x][1] = attachments[x][1].replace(']', '')
                    await ctx.send(file=discord.File('filename/' + attachments[x][1]))
                there_is_attachment = False
                attachments = []
                paginator.clear()
            else:
                await ctx.send(embed=embed)
                for page in paginator.pages:
                    await ctx.send(page)
                paginator.clear()


@bot.command()
async def last(ctx):
    """Afficher le dernier mail reçu."""
    await send_all_data(ctx.channel)


bot.loop.create_task(check_new_mail())
bot.run(TOKEN)