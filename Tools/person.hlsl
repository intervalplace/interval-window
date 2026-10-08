// A PERSON, NOT A MANNEQUIN.
//
// The only skeleton this project has is the engine's grey figure, and grey
// plastic is a costume like any other -- it just happens to be a shop dummy's.
// There is no texture to put on it and no UV layout worth trusting, so the
// clothes are drawn the way the half-timbering is: from POSITION, banded up
// the body.
//
// WHERE THE BODY IS, MEASURED FROM ITS FEET. The obvious way to do this is a
// world-to-local transform in the graph, and it comes back constant on a
// skinned mesh: every pixel gets the same answer and the whole figure ends up
// one flat colour. So the two things this needs are handed in instead, by
// whatever placed the figure this frame and therefore knows them exactly --
// `Foot`, where they are standing, and `Fore`, which way they are facing.
//
// `Who` is the citizen's own number. A street where everyone wears the same
// tunic is the same fault as a street where every house has the same walls.

// SCALED BY THEIR OWN BUILD. The bands below are in centimetres up a person
// of ordinary height, and citizens are not all of ordinary height -- so the
// measurement is taken in that person's own proportion. Without it a short
// citizen wears their belt round their chest.
float  H    = (W.z - Foot.z) / max(Tall, 0.5);  // how far up the body
float2 Out  = W.xy - Foot.xy;                   // out from the spine
float  Side = length(Out);                      // rotation does not matter
float2 Ahead = normalize(Fore.xy + float2(1e-5, 0.0));
float  Front = dot(Out, Ahead);
float  h    = saturate(Who);

// ---- WHAT THEY ARE WEARING ----
//
// THE SAME DYES THE BROWSER WINDOW USES, from the same number. That window
// reads the first eight hex digits of a citizen's id and derives their whole
// appearance from it: the tunic is a hue off the key at a fixed saturation and
// lightness, the skin is one of six, the hair one of seven. Deriving our own
// would dress the same person two ways in two windows, and "the woman in the
// blue kirtle" would stop being a sentence anybody could act on.
//
// Hue to colour, written out because a material has no library: this is the
// standard HSL wheel, three ramps a third of a turn apart.
float3 Hsl;
{
    float H6 = frac(Hue) * 6.0;
    float S = 0.42, L = 0.34;
    float Cc = (1.0 - abs(2.0 * L - 1.0)) * S;
    float X = Cc * (1.0 - abs(fmod(H6, 2.0) - 1.0));
    float Mm = L - Cc * 0.5;
    float3 R = (H6 < 1.0) ? float3(Cc, X, 0) : (H6 < 2.0) ? float3(X, Cc, 0)
             : (H6 < 3.0) ? float3(0, Cc, X) : (H6 < 4.0) ? float3(0, X, Cc)
             : (H6 < 5.0) ? float3(X, 0, Cc) : float3(Cc, 0, X);
    Hsl = R + Mm;
}

float3 Tunic   = Hsl;
// HOSE ARE NOT THE TUNIC. Tinted from the same hue the whole figure came out
// one colour, head to boot, which is not how anybody has ever dressed: the dye
// went on the garment that showed. The browser window puts a dark neutral on
// the hips for the same reason, and this is it, varied a little.
float3 Hose = pow(float3(0.184, 0.157, 0.125), 2.2) * (0.74 + 0.62 * frac(Who * 7.1));
float3 Leather = float3(0.056, 0.038, 0.026) * (0.8 + 0.5 * frac(Who * 3.3));
float3 Linen   = float3(0.210, 0.198, 0.170);

// The six skins and the seven hairs, in the browser window's own order.
float3 Skins[6];
Skins[0] = float3(0.910, 0.788, 0.627); Skins[1] = float3(0.851, 0.659, 0.467);
Skins[2] = float3(0.788, 0.541, 0.369); Skins[3] = float3(0.659, 0.447, 0.290);
Skins[4] = float3(0.541, 0.353, 0.227); Skins[5] = float3(0.420, 0.267, 0.157);
float3 Hairs[7];
Hairs[0] = float3(0.165, 0.125, 0.094); Hairs[1] = float3(0.290, 0.204, 0.125);
Hairs[2] = float3(0.420, 0.290, 0.165); Hairs[3] = float3(0.541, 0.416, 0.227);
Hairs[4] = float3(0.102, 0.102, 0.102); Hairs[5] = float3(0.620, 0.227, 0.102);
Hairs[6] = float3(0.722, 0.690, 0.627);

int Si = clamp((int)(Skin + 0.5), 0, 5);
int Hi = clamp((int)(Hair + 0.5), 0, 6);
// Those are sRGB bytes off a web page; the renderer works in linear light, and
// a colour pasted across without that step comes out washed and chalky.
float3 SkinC = pow(Skins[Si], 2.2);
float3 HairC = pow(Hairs[Hi], 2.2);
float3 Skin3 = SkinC;

// ---- THE BANDS ----
// A mannequin is about 180cm and stands on its feet, so these are centimetres
// up a person: boots, hose, belt, tunic to the collarbone, a collar, a hood.
float3 C = Tunic;
float  R = 0.88;

// A tunic came to the knee or thereabouts and the hose showed below it, with
// the belt worn at the waist OVER the tunic -- so the belt is a band inside
// the tunic's range rather than the join between two garments.
if      (H <  14.0) { C = Leather;      R = 0.60; }
else if (H <  58.0) { C = Hose;         R = 0.90; }
else if (H <  97.0) { C = Tunic;        R = 0.88; }   // the skirt of it
else if (H < 105.0) { C = Leather;      R = 0.54; }
else if (H < 150.0) { C = Tunic;        R = 0.88; }
else if (H < 160.0) { C = Linen;        R = 0.84; }
else                { C = HairC;        R = 0.92; }   // under the hood

// The face, where a hood opens: forward of the spine, in the top band only, so
// a turned head keeps its hood and a bowed one does not lose its face.
float Face = step(160.0, H) * step(H, 177.0) * smoothstep(1.0, 6.0, Front);
C = lerp(C, Skin3, Face);
R = lerp(R, 0.50, Face);

// EYES AND A BROW. Two dark marks and a line above them is the whole of what
// a face has to be at the distance anybody is ever seen from -- and without
// them a head is an egg, which is the other half of why a dressed figure
// still read as a dummy. Across the face rather than out from the spine: the
// sideways direction is the one perpendicular to the way they are looking.
float Across = abs(dot(Out, float2(-Ahead.y, Ahead.x)));
float Eyes = Face
    * smoothstep(3.2, 4.0, Across) * (1.0 - smoothstep(6.2, 7.2, Across))
    * smoothstep(166.0, 167.4, H) * (1.0 - smoothstep(170.0, 171.4, H));
float Brow = Face * (1.0 - smoothstep(7.8, 9.0, Across))
    * smoothstep(171.6, 172.4, H) * (1.0 - smoothstep(174.0, 175.0, H));
float Dark = saturate(Eyes + Brow * 0.7);
C = lerp(C, Skin3 * 0.22, Dark);

// Hands. The sleeve stops at the wrist, and a hand at rest hangs at the hip,
// so height alone cannot find it -- but a hand is always further out from the
// spine than a hip is.
// FURTHER OUT THAN A HIP IS. At twenty centimetres this caught the hips and
// put a patch of bare skin across the seat of every citizen's hose: a hip is
// about that far from the spine and a hand at rest is a good deal further.
float Hand = smoothstep(23.0, 27.0, Side) * step(62.0, H) * step(H, 108.0);
C = lerp(C, Skin3, Hand);
R = lerp(R, 0.52, Hand);

// ---- WOVEN, AND WORN ----
// Cloth at this distance is a value, not a weave, but a little grain stops it
// reading as paint; and everything is dirtier at the hem than at the shoulder,
// because that is the end that meets the road.
float Weave = sin(W.x * 2.9 + W.y * 3.3) * 0.5 + sin(H * 5.1) * 0.5;
C *= 1.0 + 0.05 * Weave;
C *= lerp(0.72, 1.0, saturate((H - 4.0) / 60.0));

// ---- AND THE SHAPE OF THEM ----
//
// A material is not only paint. It is also asked, every frame, where each
// vertex should BE -- and that is the answer to "can we do nothing about the
// form of the figure". There is one mesh and it is a shop dummy with an
// athlete's chest and a waist like a wasp, and no amount of colour fixes that.
// Moving the vertices does.
//
// Everything here is centimetres, pushed along the direction out from the
// spine, banded up the body the same way the cloth is, and taken from the
// citizen's OWN number -- so one is stout and one is spare and one stoops, and
// each of them is the same shape tomorrow and in every other window that
// computes it. It happens after skinning, so it survives the animation.
float Stout   = frac(h * 11.3);
float Stoop   = frac(h * 19.7);
float Shoulder = frac(h * 5.1);

float2 Flat = Out;
float  Away = length(Flat);
float2 Dir  = Away > 0.5 ? Flat / Away : float2(0.0, 0.0);

float Push = 0.0;
// The tunic is loose cloth over a body, not a second skin: everything from
// the hip to the collarbone stands off.
Push += smoothstep(66.0, 80.0, H) * (1.0 - smoothstep(142.0, 156.0, H))
      * (2.6 + 3.4 * Stout);
// The legs are slighter than the figure's own. So is the chest, which is the
// single most dummy-like thing about it.
Push -= smoothstep(64.0, 44.0, H) * 0.9;
Push -= (1.0 - smoothstep(118.0, 132.0, H)) * smoothstep(104.0, 118.0, H) * 0.8;
// SHOULDERS. The figure is a comic-book athlete: a shelf of deltoid and a
// waist like a wasp, which is most of what still read as "not a person" once
// it was dressed. So the baseline comes IN, and breadth is then given back
// only to the citizens whose number says they are broad.
Push += smoothstep(138.0, 150.0, H) * (1.0 - smoothstep(158.0, 168.0, H))
      * (-1.7 + 3.4 * Shoulder);
// Arms, which on this mesh are a bodybuilder's. Anything this far out from
// the spine at chest height is a limb.
Push -= smoothstep(19.0, 26.0, Side) * smoothstep(96.0, 112.0, H)
      * (1.0 - smoothstep(150.0, 164.0, H)) * 1.1;
// And the head, which is a shade small: stylised figures shrink it, people
// notice without knowing why.

Push += smoothstep(158.0, 166.0, H) * 0.7;

float3 Move = float3(Dir * Push, 0.0);

// A belly is in FRONT, not all the way round, and a stoop carries the
// shoulders forward of the feet. Both are what say somebody has lived a while.
float Belly = smoothstep(86.0, 104.0, H) * (1.0 - smoothstep(120.0, 138.0, H))
            * saturate(dot(Dir, Ahead)) * Stout * 3.8;
float Bend = saturate((H - 104.0) / 70.0) * Stoop * 4.4;
Move.xy += Ahead * (Belly + Bend);
Move.z -= Bend * 0.5;

Shape = Move;

Rough = R;
return C;
