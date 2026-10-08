// THE NIGHT SKY, DRAWN RATHER THAN PHOTOGRAPHED.
//
// The window has had a sky atmosphere since the beginning and at night it is
// an empty dark blue dome. A night sky with nothing in it is the single
// loudest thing a world can get wrong after dark, because everyone has seen
// the real one.
//
// AT INFINITY, WHICH IS WHY THERE IS NO DOME POSITION IN HERE. The direction
// used is the VIEW RAY -- the vector from the camera through this pixel -- so
// the stars do not move when the camera does, whatever size the sphere
// carrying them happens to be or where it is centred. A dome that has to be
// the right size is a dome that will one day be the wrong size.
float3 D = normalize(-Eye);

// ---- WHICH PATCH OF SKY ----
//
// Cube-face mapping, not spherical. Longitude and latitude bunch the cells
// together at the poles: with a plain (atan2, acos) mapping the zenith comes
// out as a bright knot of stars directly overhead, which is exactly where a
// top-down window looks. Six flat faces have no poles to bunch at.
float3 A = abs(D);
float  M = max(A.x, max(A.y, A.z));
float2 UV;
float  Face;
if (A.x >= M)      { UV = D.yz / max(A.x, 1e-4); Face = (D.x > 0.0) ? 0.0 : 1.0; }
else if (A.y >= M) { UV = D.xz / max(A.y, 1e-4); Face = (D.y > 0.0) ? 2.0 : 3.0; }
else               { UV = D.xy / max(A.z, 1e-4); Face = (D.z > 0.0) ? 4.0 : 5.0; }

float  Cells = 150.0;
float2 G  = UV * Cells;
float2 Id = floor(G);

float3 Sky = 0.0;
for (int j = -1; j <= 1; ++j)
{
	for (int i = -1; i <= 1; ++i)
	{
		float2 C = Id + float2(i, j);
		float2 K = C + Face * 37.13;
		float h1 = frac(sin(dot(K, float2(127.1, 311.7))) * 43758.5453);
		float h2 = frac(sin(dot(K, float2(269.5, 183.3))) * 27182.8459);
		float h3 = frac(sin(dot(K, float2(419.2, 371.9))) * 16807.0517);

		// MOST OF THE SKY IS EMPTY. A star in every cell is graph paper; a
		// third of cells, placed anywhere within their own, has no grid left
		// in it that the eye can find.
		if (h3 > 0.34) { continue; }

		float2 At = C + float2(h1, h2);
		float  d  = length(G - At);

		// THE MAGNITUDES ARE NOT EVEN. A real sky has a dozen bright stars, a
		// few hundred ordinary ones and thousands at the edge of seeing, and
		// the cube of a uniform number is a fair-enough version of that. Even
		// brightness reads as a scattering of identical dots, which is the
		// other way to get this wrong.
		float mag = pow(frac(h3 * 91.7 + h1 * 3.1), 3.0);
		float core = exp(-pow(d * 26.0, 2.0));
		float halo = exp(-pow(d *  7.0, 2.0)) * 0.22;

		// AND THEY TWINKLE, slowly and each on its own. Air, not the star.
		float tw = 0.78 + 0.22 * sin(Time * (1.7 + h1 * 2.9) + h2 * 62.83);

		// Hot stars are blue and cool ones amber, and the bright ones are more
		// often blue, which is why a real sky looks faintly cold.
		float3 tint = lerp(float3(1.00, 0.84, 0.66), float3(0.76, 0.86, 1.00),
		                   saturate(mag * 1.6 + h2 * 0.35));
		Sky += tint * (core + halo) * (0.06 + 0.94 * mag) * tw;
	}
}

// ---- THE MILKY WAY ----
//
// One broad band, because the alternative is a sky that is uniformly speckled
// and therefore uniformly uninteresting. The band's own axis is arbitrary and
// fixed: this island has one sky and it is the same sky every night.
float3 Pole = normalize(float3(0.36, -0.72, 0.59));
float  Off  = abs(dot(D, Pole));
float  Band = exp(-pow(Off * 3.4, 2.0));
// Clumped rather than smooth, or it is a searchlight beam across the sky.
float  n1 = sin(D.x * 11.3 + D.y * 7.7) + 0.7 * sin(D.y * 19.1 - D.z * 13.3 + 2.1);
float  n2 = sin(D.z * 31.7 + D.x * 23.9 - 1.4);
float  Milk = Band * saturate(0.42 + 0.30 * n1 + 0.16 * n2);
Sky += float3(0.62, 0.66, 0.82) * Milk * 0.055;

// ---- AND IT IS ONLY THERE WHEN IT IS DARK ----
//
// `Night` is one minus how much daylight the world says there is, off the one
// collection the hour writes to. Squared, because the stars go out a good deal
// faster than the light comes up -- by the time the sky is properly blue there
// is nothing left to see, and a star visible over a lit village at dusk is the
// tell that this is a painted dome.
float Dark = saturate(Night);
Dark = Dark * Dark * Dark;

// BELOW THE HORIZON THERE ARE NO STARS, because below the horizon there is
// ground, and the dome is bigger than the island. Faded rather than cut so the
// join is not a line.
float Above = smoothstep(-0.06, 0.10, D.z);

return Sky * Dark * Above * Bright;
