// THE MASTER MATERIAL FOR FLAT-COLOURED ART.
//
// The Quaternius people carry no texture at all. Every region of a figure is
// its own material with its own name -- Skin, Hair, Eye, Brown, Beige, Gold --
// and a single diffuse colour. That is far better than an atlas: the art tells
// us what each surface IS, by name, so nothing has to be guessed from the
// pixels the way the old cloth-detector guessed from saturation.
//
// So `Strength` is not a switch, it is HOW MUCH THIS REGION MAY VARY, set once
// per material from its name when the art is re-parented. Eyes never vary.
// Skin varies a little. Cloth varies most. `Shift` is the citizen -- one number
// off their own key, the same number the browser window derives -- and it turns
// the colour around the wheel without touching how light or how saturated the
// artist made it. A farmer stays a farmer, red kerchief over beige shirt; THIS
// farmer is simply not the same farmer as the one in the next field.

float3 C = max(Base, 0.0);

// --- to hue/saturation/value ---
float Mx = max(C.r, max(C.g, C.b));
float Mn = min(C.r, min(C.g, C.b));
float Chroma = Mx - Mn;
float H = 0.0;
if (Chroma > 1e-5)
{
	if (Mx == C.r)      { H = (C.g - C.b) / Chroma; }
	else if (Mx == C.g) { H = (C.b - C.r) / Chroma + 2.0; }
	else                { H = (C.r - C.g) / Chroma + 4.0; }
	H = frac(H / 6.0 + 1.0);
}
float S = (Mx > 1e-5) ? Chroma / Mx : 0.0;

// --- turn it, by this citizen, by as much as this region allows ---
// Centred on zero so half a street shifts warm and half shifts cool, rather
// than everybody drifting the same way from the artist's colour.
H = frac(H + (Shift - 0.5) * 0.28 * saturate(Strength) + 1.0);

// --- back again ---
float  h6 = H * 6.0;
float  X  = Chroma * (1.0 - abs(fmod(h6, 2.0) - 1.0));
float3 R  = (h6 < 1.0) ? float3(Chroma, X, 0.0)
          : (h6 < 2.0) ? float3(X, Chroma, 0.0)
          : (h6 < 3.0) ? float3(0.0, Chroma, X)
          : (h6 < 4.0) ? float3(0.0, X, Chroma)
          : (h6 < 5.0) ? float3(X, 0.0, Chroma)
                       : float3(Chroma, 0.0, X);
C = R + Mn;

// ---------------------------------------------------------------------------
// GRAIN, AND COURSES.
//
// Everything built out of this material is a flat colour over an untextured
// box, and at the scale of a cottage that reads as a cottage. At the scale of
// a six-and-a-half-metre town wall it reads as cardboard: one continuous tone
// across forty square metres, which no material anybody has ever built a wall
// out of does.
//
// Both effects are pure functions of WORLD position. That matters twice over:
// the joint between two wall segments does not show, because neither segment
// has UVs of its own to disagree about; and every window that computes this
// gets the same stones in the same places, which is the rule everything else
// in this project follows.

// WHICH PLANE TO LAY THE STONES IN. A wall's courses run round it and a
// walkway's flags lie flat, so the two axes are picked off the face's own
// normal: near-horizontal takes the ground plane, otherwise the vertical plane
// facing the way it faces. Three cases, no blending -- a box has no corners
// worth blending across.
float Dry = saturate(DryRough);
float3 Nn = normalize(Norm);
float2 uv = (abs(Nn.z) > 0.7) ? Wp.xy
          : ((abs(Nn.x) > abs(Nn.y)) ? float2(Wp.y, Wp.z) : float2(Wp.x, Wp.z));

// A little mottle at two scales, for anything at all. Plane waves crossing at
// angles that share no common period; a product of two sines is a grid and
// makes the whole island tartan, which is written up in ground.hlsl.
float a1 = Wp.x * 0.0091 + Wp.y * 0.0067 + Wp.z * 0.0043;
float b1 = Wp.x * -0.0053 + Wp.y * 0.0111 + 2.1;
float a2 = Wp.x * 0.0620 - Wp.z * 0.0480 + 0.7;
float b2 = Wp.y * 0.0510 + Wp.z * 0.0390 - 1.8;
float g1 = sin(a1) + 0.7 * sin(b1);
float g2 = sin(a2) + 0.7 * sin(b2);
C *= 1.0 + saturate(Grain) * (g1 * 0.42 + g2 * 0.26);

// ---- AND THE SAME MOTTLE AS RELIEF ----
//
// Everything built in this window was a flat colour on a flat facet, and from
// any angle where the sun was not raking it that reads as painted card. The
// mottle above was already there and was doing half the job: it says the
// surface is not uniform, and says nothing about it having a surface.
//
// The slope is taken ANALYTICALLY from the same waves, not by differencing a
// sampled height -- which is how a procedural normal ends up as a lattice, and
// is written up at length in ground.hlsl. It is then flattened onto the face,
// so a slope worked out in world space does not tip a wall off its own plane.
float3 Rough3 = cos(a2) * float3(0.0620, 0.0, -0.0480)
              + 0.7 * cos(b2) * float3(0.0, 0.0510, 0.0390);
Rough3 = (Rough3 - dot(Rough3, Nn) * Nn) * saturate(Grain) * 2.2;

// WHICH TWO WORLD AXES THE uv PLANE WAS LAID IN. A groove worked out in uv --
// a mortar line, a gap between boards -- has to be put back into the world,
// and the plane it was measured in is the one chosen just above.
float3 Ax0, Ax1;
if (abs(Nn.z) > 0.7)                 { Ax0 = float3(1, 0, 0); Ax1 = float3(0, 1, 0); }
else if (abs(Nn.x) > abs(Nn.y))      { Ax0 = float3(0, 1, 0); Ax1 = float3(0, 0, 1); }
else                                 { Ax0 = float3(1, 0, 0); Ax1 = float3(0, 0, 1); }
float2 Cut = 0.0;   // slope out of whatever grooves this surface has

// ---- BOARDS, OR COURSES OF THATCH ----
//
// `Plank` is how far apart the lines run, in centimetres, and zero is "this
// surface has none" -- which is most things. It exists for the two surfaces
// that are enormous on screen and were a single flat colour: a roof and a
// timber wall. A hall's roof at four hundred metres is a tan slab the size of
// a thumbnail, and one line across it every thirty centimetres is the whole
// difference between a roof and a ramp.
if (Plank > 1.0)
{
	float rowp  = uv.y / Plank;
	float bandp = frac(rowp);
	float dp    = (bandp < 0.5) ? bandp : (bandp - 1.0);
	float Gp    = exp(-pow(dp / 0.075, 2.0));
	C *= lerp(1.0, 0.78, Gp);
	// No two boards out of a wood are the same, and no two courses of thatch
	// were cut in the same week.
	float ownp = frac(sin(floor(rowp) * 78.233 + 11.7) * 43758.5453);
	C *= 0.93 + 0.14 * ownp;
	Cut.y += (dp < 0.0 ? -1.0 : 1.0) * Gp * 0.80;
}

// AND THE STONES THEMSELVES, where something says how tall a course is.
// Zero is "this is not masonry", which is timber, thatch, cloth and everybody
// wearing them.
if (Course > 1.0)
{
	float row   = uv.y / Course;
	float band  = frac(row);
	// Every other course offset by half a block, because that is how a wall
	// that stays up is laid -- a stack of aligned joints is a crack.
	float shift = (fmod(floor(row), 2.0) < 1.0) ? 0.0 : 0.5;
	float col   = uv.x / (Course * 2.05) + shift;
	float vgap  = frac(col);

	// The mortar is the thin dark line where neither the course nor the joint
	// is in the middle of a face.
	float near  = min(min(band, 1.0 - band), min(vgap, 1.0 - vgap));
	float face  = smoothstep(0.0, 0.055, near);
	C *= lerp(0.58, 1.0, face);

	// AND IT IS A GROOVE, not a painted line. A mortar joint is set back from
	// the stones either side of it, and the thin shadow that puts along the
	// underside of every course is most of what tells a wall from a photograph
	// of one -- which is what the painted version was.
	float dv = (band < 0.5) ? band : (band - 1.0);
	float du = (vgap < 0.5) ? vgap : (vgap - 1.0);
	Cut += float2((du < 0.0 ? -1.0 : 1.0) * exp(-pow(du / 0.045, 2.0)),
	              (dv < 0.0 ? -1.0 : 1.0) * exp(-pow(dv / 0.045, 2.0))) * 0.85;

	// And no two stones out of a quarry are the same colour.
	float2 id   = float2(floor(col), floor(row));
	float  own  = frac(sin(dot(id, float2(127.1, 311.7))) * 43758.5453);
	C *= 0.90 + 0.20 * own;
	Dry = 0.94;
}

// Rain darkens whatever it lands on and tightens the highlight, the same way
// it does to the ground -- read from the one collection the hour writes to, so
// a citizen is wet in the same weather as the field they stand in.
float W = saturate(Wet);
C *= lerp(1.0, 0.74, W);
Rough = lerp(Dry, Dry * 0.5, W);

// ---- AND IT ALL GOES AWAY AT A DISTANCE ----
//
// A mortar joint is half a centimetre wide. Held all the way out it is far
// under a pixel by the time a wall is across a valley, and a sub-pixel groove
// is not detail, it is a surface that crawls when the camera moves. Faded from
// nine metres and gone by forty, which is past everything the watch camera
// holds.
float NearBy = saturate(1.0 - (length(CamPos - Wp) - 900.0) / 3100.0);
Normal = normalize(Nn + (Cut.x * Ax0 + Cut.y * Ax1 + Rough3) * NearBy);
return C;
