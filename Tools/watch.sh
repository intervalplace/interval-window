#!/bin/bash
# Serve the Unreal window itself to a phone, over the LAN.
#
# This is Pixel Streaming: the editor encodes its viewport with VideoToolbox and
# sends it over WebRTC, so the phone gets the SAME pixels the editor draws --
# not a second window into the world. The citizen is untouched by it; the key
# stays where it has always been, in the bridge.
#
# Two processes:
#   * this script -- Epic's signalling server, which serves player.html on
#     PLAYER_PORT and brokers WebRTC on STREAMER_PORT
#   * the editor  -- launched by ue.sh with UE_STREAM=1, which connects to
#     STREAMER_PORT as a streamer
#
# The engine's own copy of this server would do, but it defaults its viewer port
# to 80 (root, on macOS) and re-runs get_ps_servers.sh on every start -- which
# deletes the frontend build. Running it here sidesteps both.
set -e
W="/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Media/PixelStreaming2/Resources/WebServers/SignallingWebServer"
PLAYER_PORT=${PLAYER_PORT:-8080}
STREAMER_PORT=${STREAMER_PORT:-8888}
# THE ADDRESS HAS A SHELF LIFE, so print the name as well.
#
# A raw IP is whatever interface the Mac happened to be using when this ran:
# move between networks -- or just hand off from en0 to en1 -- and the link
# that was working stops working, from the phone's side looking exactly like a
# WiFi fault. It cost a round of "are you both on the same network?" once.
# The Bonjour name follows the machine, so that is the one to keep.
IP=""
for _if in en0 en1 en5 en6; do
  IP=$(ipconfig getifaddr "$_if" 2>/dev/null) && [ -n "$IP" ] && break
done
[ -z "$IP" ] && IP=127.0.0.1
HOSTNAME_LOCAL="$(scutil --get LocalHostName 2>/dev/null).local"

if [ ! -f "$W/www/player.html" ]; then
  echo "frontend not built: run npm install && npm run build:all:cjs in $(dirname "$W")" >&2
  exit 1
fi

echo "the window will be at  http://$HOSTNAME_LOCAL:$PLAYER_PORT/   <- use this one on the phone"
echo "                   or  http://$IP:$PLAYER_PORT/          (this address changes with the network)"
echo "the editor connects to ws://127.0.0.1:$STREAMER_PORT"
# ---- THE TUNNEL WANTS --protocol http2 ON THIS NETWORK ----
#
# `cloudflared tunnel --url http://localhost:8080` prints a trycloudflare
# hostname and reports a registered connection, and the hostname then never
# resolves: NXDOMAIN for as long as anybody is willing to wait, and the phone
# says ERR_NAME_NOT_RESOLVED. The tunnel is not broken and the URL is not
# stale -- cloudflared's own precheck says why, several lines below the URL:
#
#   precheck ... UDP Connectivity ... QUIC connection failed ... region2
#   ERROR: Allow outbound QUIC traffic on port 7844 or use HTTP2.
#   precheck complete hard_fail=true
#
# Something on this network blocks QUIC to one of the two regions, the quick
# tunnel is never fully provisioned, and the name is never published. Forcing
# the older transport fixes it outright:
#
#   cloudflared tunnel --protocol http2 --url http://localhost:8080
#
# The hostname is new every time cloudflared starts; there is no keeping one.

# ---- AND A STUN SERVER, SO IT WORKS FROM OFF THIS NETWORK ----
#
# On the LAN the two ends can see each other and WebRTC needs nothing. Through
# a tunnel they cannot: the phone is on mobile data, the Mac is behind a home
# router, and neither knows an address the other can reach. STUN is how each
# end finds out what the world sees it as, and it is enough for most home NATs.
#
# It is NOT enough for all of them. Behind a symmetric NAT the pair need a
# relay -- a TURN server -- which means the video passes through somebody
# else's machine. That is a real privacy cost and it is not taken here without
# being asked for; if the stream connects and then shows nothing, this is the
# reason and TURN is the fix.
PEER_OPTS=${PEER_OPTS:-'{"iceServers":[{"urls":["stun:stun.l.google.com:19302","stun:stun1.l.google.com:19302"]}]}'}

exec node "$W/dist/index.js" --serve \
  --http_root "$W/www" --homepage player.html \
  --player_port "$PLAYER_PORT" --streamer_port "$STREAMER_PORT" \
  --peer_options "$PEER_OPTS" \
  --console_messages verbose
