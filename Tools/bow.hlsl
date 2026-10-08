// A RAINBOW, WHICH THE WORLD HAS BEEN REPORTING ALL ALONG.
//
// The bridge sends a `rainbow` in every frame's sky and the window has never
// once drawn it. Asked for from the stream, in a list of the things that would
// lift this place most: "maybe occasional rainbow after rain".
//
// IT IS BUILT FROM THE GEOMETRY AND NOT FROM A TEXTURE. A rainbow is not a
// decoration that can be placed; it is an angle. Every drop of water in the
// air throws sunlight back at about forty-two degrees from the direction the
// light came from, so what a person sees is a circle of that radius centred on
// the shadow of their own head -- the antisolar point. Move, and it moves with
// you; that is why you cannot walk up to one. Drawing it from the view ray and
// the sun gives all of that for nothing, and gives it correctly when the
// camera turns, which a painted arc would not.
//
// AT INFINITY, like the stars on the same kind of dome: the direction used is
// the view ray, so the sphere's size and centre never enter into it.
float3 D = normalize(-Eye);
float3 S = normalize(Sun);

// ---- HOW FAR THIS PIXEL IS FROM THE ANTISOLAR POINT ----
//
// `-S` is the direction away from the sun, which is where the middle of the
// bow's circle sits. The angle out from there is what decides the colour.
float  C = clamp(dot(D, -S), -1.0, 1.0);
float  Ang = degrees(acos(C));

float3 Light = 0.0;

// ---- THE PRIMARY BOW ----
//
// Red at 42.4 degrees out and violet at 40.6, and that order is not a detail:
// in the primary bow red is on the OUTSIDE, which is the one thing everybody
// half-remembers and notices when it is wrong. Light inside forty degrees is
// the reason the sky within the bow is measurably brighter than the sky
// outside it -- Alexander's band -- and that is drawn too, faintly, because it
// is most of what makes a real one look like it is made of light.
float T1 = saturate((42.6 - Ang) / 2.1);          // 0 at red, 1 at violet
float Band1 = smoothstep(0.0, 0.10, T1) * smoothstep(0.0, 0.10, 1.0 - T1);

// The spectrum, as three overlapping humps rather than a hue wheel: a hue
// ramp gives equal weight to every colour and a rainbow does not -- the green
// and the red carry it and the indigo is a rumour.
float3 Hue1;
Hue1.r = exp(-pow((T1 - 0.06) * 3.1, 2.0)) * 1.00
       + exp(-pow((T1 - 0.92) * 4.0, 2.0)) * 0.55;   // violet is red-ish again
Hue1.g = exp(-pow((T1 - 0.42) * 3.0, 2.0)) * 0.92;
Hue1.b = exp(-pow((T1 - 0.80) * 2.8, 2.0)) * 0.95;
Light += Hue1 * Band1 * 0.85;

// ---- AND THE SECONDARY, WHICH IS USUALLY THERE AND USUALLY MISSED ----
//
// Fifty-one degrees out, about a tenth the brightness, and with the colours
// the other way round because the light inside it has bounced twice. Leaving
// it out is what makes a drawn rainbow look drawn.
float T2 = saturate((Ang - 50.2) / 3.2);
float Band2 = smoothstep(0.0, 0.14, T2) * smoothstep(0.0, 0.14, 1.0 - T2);
float3 Hue2;
Hue2.r = exp(-pow((T2 - 0.94) * 3.1, 2.0)) * 1.00;
Hue2.g = exp(-pow((T2 - 0.50) * 3.0, 2.0)) * 0.92;
Hue2.b = exp(-pow((T2 - 0.10) * 2.8, 2.0)) * 0.95;
Light += Hue2 * Band2 * 0.11;

// ALEXANDER'S BAND: brighter inside the primary than between the two bows.
Light += 0.020 * saturate((40.2 - Ang) / 6.0);

// ---- AND WHERE IT IS NOT ----
//
// BELOW THE HORIZON THERE IS NO BOW, because there is no sky to put it on and
// because the drops that make it are lit from above. The dome reaches under
// the ground and without this the arc closes into a full ring under the
// island, which reads as a hoop the world is sitting inside.
Light *= smoothstep(-0.02, 0.10, D.z);

// AND NO BOW WITH THE SUN HIGH. The antisolar point is as far below the
// horizon as the sun is above it, so once the sun passes forty-two degrees
// the whole circle is underground and there is nothing to see. This is why
// rainbows belong to the morning and the late afternoon, and having it come
// out of the arithmetic rather than out of a schedule means it is right on a
// midsummer noon without anybody deciding anything.
Light *= smoothstep(44.0, 36.0, degrees(asin(clamp(S.z, -1.0, 1.0))));

// AND NOTHING AT NIGHT. A moonbow is real and is not this.
return Light * saturate(Bow) * saturate(Day * 1.4);
