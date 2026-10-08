// HOW A HANGING THING SWINGS, as a world position offset.
//
// The old chain hangs from a fist and the first cut of it stood out from the
// hand like an arrow. That was reported from the stream in those words -- "it
// should also sway, not be straight like an arrow" -- and it is the same
// fault the grass had: a thing that is loose and does not move reads as a
// stick painted to look like the thing.
//
// A PENDULUM, NOT A NOISE FIELD. wind.hlsl drives grass from WORLD position,
// because a field of grass is one field and the gust crosses it. A chain is
// one object hanging from one point, and what it does is swing about that
// point: the amplitude has to grow with the distance DOWN the run and be zero
// at the grip, or the whole chain slides sideways in the hand.
//
//   Local   the vertex in the object's own space. The chain is built with its
//           grip at the origin running down -z, so -Local.z is how far down
//           the run this vertex is. Anything else that hangs must be built
//           the same way; see chain() in make_art.py.
//   Length  how long the run is, in centimetres, so Drop comes out 0..1
//           without this file having to know which object it is on.
//   Side    the object's own X axis in world space, which is the direction
//           the swing travels in. Passed in rather than assumed, because a
//           chain in a hand is turned by whatever the hand is doing.
//   Fore    the object's Y axis, likewise, for the smaller second beat.
//   Amp     centimetres of travel at the very tip.
//   Time    the game's own clock.
//
// TWO BEATS, AT AN AWKWARD RATIO. One sine is a metronome and reads as a
// mechanism. 1.0 and 0.63 do not divide into each other, so the tip traces a
// slow open figure that never repeats where anybody can see it repeat, which
// is what a hanging chain actually does.
//
// AND AT A PENDULUM'S OWN RATE. A chain ninety centimetres long swings with a
// period near two seconds -- sqrt(length over g), which is not a matter of
// taste -- so the rate here is 3.2 radians a second and not something slower
// that looked calm in a still. The grass in this window was once reported as
// "waving like an ocean" for exactly that mistake, and a chain drifting at a
// fifth of its own rate reads as seaweed in the same way.

float Drop = saturate(-Local.z / max(Length, 1.0));
// CUBED, NEARLY. A pendulum's displacement is linear in the distance from the
// pivot; a chain is not rigid and the slack gathers at the bottom, so the
// bottom third does most of the moving. 2.2 was chosen by watching it.
float Fall = pow(Drop, 2.2);

// A LITTLE PER-OBJECT PHASE, so two citizens carrying chains are not swinging
// in step. The object's own position rounded to the metre is stable while it
// is carried and different for each one.
float Own = frac(sin(dot(floor(Pivot.xy * 0.01), float2(12.9898, 78.233))) * 43758.5);
float T = Time * 3.2 + Own * 6.283;

float A = Amp * Fall;
float3 Move = Side * (A * sin(T))
            + Fore * (A * 0.42 * sin(T * 0.63 + 1.7));

// AND IT DOES NOT GET LONGER. A swing about a fixed point keeps its radius:
// displace a hanging point sideways without lifting it and the chain stretches
// by the same amount it swings, which at the tip is visible as the links
// pulling apart. Lifting by the sagitta keeps the run the length it is.
float R = max(Drop * Length, 1.0);
float S = length(Move);
float3 Up = normalize(Side * 0.0 + float3(0.0, 0.0, 1.0));
Move += Up * (R - sqrt(max(R * R - S * S, 0.0)));

return Move;
