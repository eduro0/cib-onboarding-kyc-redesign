# Gem / custom GPT pack

The same assistant as `assistant/` (the Python prototype), set up as a Gemini Gem or a ChatGPT custom GPT so it
runs on Google's or OpenAI's own tools. The difference to keep in mind: here the model does the checking itself,
following the checklist. In the prototype, fixed rules do the checking and the model only reads. Use the prototype
to show the control design and the Gem to show the tool.

| File | Where it goes |
|---|---|
| `instructions.md` | paste the whole text into the Gem's (or GPT's) **Instructions** box |
| `kyc-checklist.md` | upload as a **knowledge** file |
| `output-template.md` | upload as a **knowledge** file |
| `sample-pack-harbour-lantern.md` | don't upload as knowledge: attach it in a chat to try the assistant |

**Never upload real client documents** to a consumer Gem or GPT. This pack is for fictional samples only. Real
client data goes only to tools the bank has approved for it.

## Gemini Gem

Gems take knowledge files [src:google-gems-free-2025]. Google's page with the exact file limits was not checked, so the
pack keeps to two small knowledge files and short instructions.

Free Google accounts can create Gems [src:google-gems-free-2025]. Google says the Gemini web app is available
in over 230 countries and territories [src:gemini-web-app-countries]; check that Hong Kong is on its list.

Google has renamed Gems to **skills** [src:gemini-gems-now-skills]; the steps below work the same under the new
name: Customize → Skills → Create → Create manually, with Add files for the knowledge files.

1. Open gemini.google.com and choose **Gems** → **New Gem**.
2. Name it "KYC review assistant (demo)". Paste `instructions.md` into Instructions.
3. Under Knowledge, upload `kyc-checklist.md` and `output-template.md`. Save.
4. Start a chat with the Gem, attach `sample-pack-harbour-lantern.md`, and type "Review this pack."
5. Check the answer against `assistant/` output for the same pack: the same requested items (including the LIM
   Siew Ling mismatch and evidence for Lantern Holdings), and three beneficial owners at 40%, 30% and 30%.

## ChatGPT custom GPT (only if your account still allows it)

Not verified: OpenAI's help pages could not be read on 2026-11-18, and search results suggest that creating new
GPTs is closed on personal plans. Check in your account before relying on it. The Gem is the main path.


Explore GPTs → Create → Configure: paste `instructions.md` into Instructions, upload the two knowledge files,
turn off web browsing and image generation, and save it as "Only me". Test it the same way.
