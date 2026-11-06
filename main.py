import asyncio
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from animaux import ANIMAUX, trouver_animal, normaliser
from questions import QUESTIONS
from stockage import charger, sauvegarder, FICHIER_SCORES
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

donnees = charger()
scores = charger(FICHIER_SCORES)

@bot.event
async def on_ready():
    # Envoie les commandes slash a Discord au demarrage.
    await bot.tree.sync()
    print(f"Connecte en tant que {bot.user}")


# Commande prefixee : !ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong !")


# Commande slash : /salut
@bot.tree.command(name="salut", description="Le bot te dit bonjour")
async def salut(interaction: discord.Interaction):
    await interaction.response.send_message(f"Salut {interaction.user.mention} !")

@bot.command()
async def animaux(ctx):
    noms = [a["nom"] for a in ANIMAUX]
    await ctx.send("🐾 Animaux disponibles : " + ", ".join(noms))


@bot.command()
async def animal(ctx, *, nom=None):
    if nom is None:
        await ctx.send("Utilise la commande comme ça : `!animal lion`")
        return

    trouve = trouver_animal(nom)
    if trouve is None:
        await ctx.send(f"Je ne connais pas « {nom} ». Tape `!animaux` pour voir la liste.")
        return

    embed = discord.Embed(
        title=f"🐾 {trouve['nom']}",
        description=trouve["description"],
        color=discord.Color.green(),
    )
    embed.add_field(name="Habitat", value=trouve["habitat"], inline=True)
    embed.add_field(name="Régime", value=trouve["regime"], inline=True)
    await ctx.send(embed=embed)
    
@bot.command()
async def adopter(ctx, *, nom=None):
    if nom is None:
        await ctx.send("Utilise la commande comme ça : `!adopter panda`")
        return

    trouve = trouver_animal(nom)
    if trouve is None:
        await ctx.send(f"Je ne connais pas « {nom} ». Tape `!animaux` pour voir la liste.")
        return

    mes_animaux = donnees.setdefault(str(ctx.author.id), [])
    if trouve["nom"] in mes_animaux:
        await ctx.send(f"Tu as déjà adopté {trouve['nom']} !")
        return

    mes_animaux.append(trouve["nom"])
    sauvegarder(donnees)
    await ctx.send(f"🎉 {ctx.author.mention} a adopté {trouve['nom']} !")


@bot.command()
async def collection(ctx):
    mes_animaux = donnees.get(str(ctx.author.id), [])
    if not mes_animaux:
        await ctx.send("Tu n'as encore adopté aucun animal. Essaie `!adopter lion`.")
        return
    await ctx.send("🏡 Ta collection : " + ", ".join(mes_animaux))


@bot.command()
async def quiz(ctx):
    q = random.choice(QUESTIONS)
    await ctx.send(f"❓ {q['question']} (tu as 20 secondes)")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await bot.wait_for("message", check=check, timeout=20)
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Temps écoulé ! La réponse était {q['reponses'][0]}.")
        return

    if normaliser(message.content) in q["reponses"]:
        profil = scores.setdefault(
            str(ctx.author.id), {"nom": ctx.author.display_name, "points": 0}
        )
        profil["nom"] = ctx.author.display_name
        profil["points"] += 1
        sauvegarder(scores, FICHIER_SCORES)
        await ctx.send(f"✅ Bonne réponse ! Tu as {profil['points']} point(s).")
    else:
        await ctx.send(f"❌ Raté, c'était {q['reponses'][0]}.")


@bot.command()
async def score(ctx):
    profil = scores.get(str(ctx.author.id))
    points = profil["points"] if profil else 0
    await ctx.send(f"🏆 {ctx.author.mention}, tu as {points} point(s).")


@bot.command()
async def classement(ctx):
    if not scores:
        await ctx.send("Personne n'a encore de points. Lance `!quiz` !")
        return

    tri = sorted(scores.values(), key=lambda p: p["points"], reverse=True)
    lignes = [
        f"{i}. {p['nom']} : {p['points']} point(s)"
        for i, p in enumerate(tri[:5], start=1)
    ]
    await ctx.send("🏅 Classement :\n" + "\n".join(lignes))
    
    

bot.run(os.getenv("DISCORD_TOKEN"))
