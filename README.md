Sort every Emby Live-TV channel by numeric `Number` and refresh the guide.

• Works on Emby Server 4.8+ (tested 4.9.1.1 beta, June 2025).
• Moves channels bottom → top (indices don’t shift under us).
• Verifies the *entire* list; repeats (MAX_PASSES) until perfect.
• Starts the “Refresh Guide” scheduled task so UI/clients update at once.

In the "Config" secion, enter in the correct "SERVER" and "API_KEY" information. 

If you don't have an "API_KEY"

Manage Emby Server → Advanced → Api Keys → New Api Key → emby_channel_sorter → Submit

Your key is displayed under "emby_channel_sorter". Copy it and place it in the script.

Run the script: python3 emby_channel_sorter.py
