// IntervalSpan.h -- what a bridge is made of.
//
// THE WORLD HAS BRIDGES AND THIS WINDOW DREW NONE. A road that crosses water
// comes back from the generator as the ground kind `bridge`, and a bridge tile
// is a WAY, so the one thing the window did with it was refuse to sink it:
// `GroundAt` answers a way with the graded road height and answers water with
// a hundred and fifty centimetres less, and that was the whole bridge. What it
// draws is an earth causeway with the road on top of it -- solid from the
// river bed up, with nothing underneath and no water passing through. Reported
// from the stream as a cliff edge, which is exactly what it is.
//
// A bridge is a BUILT THING and has to be built. The kit this project already
// carries has both pieces for it: `BridgeSection`, a stone deck slab two and a
// half metres by two with a low kerb along each side, and
// `Column_BridgeSupport`, a four-metre pier with a base, a capital and a
// cutwater footprint. Neither was ever placed by anything.
//
// WHAT IS DELIBERATELY NOT HERE. No length, no width, no arch count, no
// pier spacing in metres. The world says which tiles are a bridge and the
// chunk reads the shape of the span off them; this asset says only what the
// stone LOOKS like, in the same way every other look in this project does.
// A level that names no deck draws no bridge and the ground is what it was.

#pragma once

#include "CoreMinimal.h"
#include "IntervalSpan.generated.h"

class UStaticMesh;
class UMaterialInterface;

/** The stone a crossing is made of. Every field is a look, never a meaning. */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalSpan
{
	GENERATED_BODY()

	/**
	 * One slab, laid once per bridge tile.
	 *
	 * MEASURED, NOT TOLD. The mesh is scaled at runtime from its own bounds so
	 * that it covers exactly one tile, which is the only arrangement in which
	 * a kit swapped for another kit still fits the ground. A number written
	 * here instead would be right for one mesh and silently wrong for the
	 * next, and the symptom -- a bridge with gaps between its slabs -- would
	 * look like a bug in the placement rather than a stale constant.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UStaticMesh> Deck;

	/** Left off to keep the mesh's own material, which the kit dressing set. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> DeckMaterial;

	/**
	 * Which way the slab faces: its local +X is taken to run ACROSS the way,
	 * because that is the axis this kit puts its kerbs on. A kit that models
	 * its deck the other way round turns it a quarter here rather than in the
	 * code, which would then be wrong for the first kit.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float DeckYaw = 0.f;

	/**
	 * HOW FAR THE KERB STANDS PROUD OF THE PAVING, in the mesh's own
	 * centimetres, so that the road is laid on the part people walk on.
	 *
	 * The slab is hung from its TOP, which is the only measurement a bounding
	 * box offers -- and on a kerbed deck the top of the box is the top of the
	 * kerb, not the surface. Hanging it from there sinks the paving by the
	 * height of the kerb and everybody on the bridge floats a hand's breadth
	 * over it. The number is measured off the mesh by `apply.py`, which can
	 * read the vertices; nothing here can.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0"))
	float DeckKerb = 0.f;

	/**
	 * A pier, stood under the edge of the deck and scaled to reach it.
	 *
	 * Also measured: its own height decides the scale, so a taller column
	 * shrinks to the same clearance rather than growing through the road.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UStaticMesh> Pier;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> PierMaterial;

	/**
	 * Tiles between one rank of piers and the next, along the span.
	 *
	 * Every tile is a pier at 1, which on a thirty-six metre crossing is
	 * eighteen columns a side and reads as a wall rather than a bridge.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "1", ClampMax = "8"))
	int32 PierEvery = 2;

	/**
	 * HOW FAR THE WATER IS DUG DOWN UNDER A CROSSING, in centimetres below the
	 * road, and the reason a bridge can be seen under at all.
	 *
	 * Water lies a hundred and fifty centimetres below the land around it,
	 * which is a river you can see is a river from above and is nowhere near
	 * enough to put a bridge over: a deck thirty-five centimetres thick leaves
	 * a metre of daylight, and a metre of daylight at this camera angle is a
	 * crack, not a crossing.
	 *
	 * THIS IS A DRAWING, NOT A DEPTH. Nothing in the world knows or cares how
	 * deep its rivers are -- the elevation field exists to route roads and
	 * nothing else reads it -- and nothing that walks, stands, floats or is
	 * placed asks this question: the chunk keeps the standing height exactly
	 * as it was and digs only the TRIANGLES. A citizen on the bridge is on the
	 * road, at the road's height, in this window and in every other.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "150", ClampMax = "900"))
	float Channel = 330.f;

	/**
	 * HOW HIGH THE WALL ALONG EACH SIDE STANDS, in centimetres, and 0 for none.
	 *
	 * The kit's deck has a kerb of its own and it is nine and a half
	 * centimetres tall: right for the scale the piece was drawn at, and
	 * invisible from a camera that looks down on the island from a long way
	 * up. A crossing with nothing along its sides reads as a paved causeway,
	 * which is the complaint this whole piece of work began from. No kit here
	 * has a parapet, a balustrade or a low wall, so the window builds one.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "300"))
	float Parapet = 78.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "5", ClampMax = "120"))
	float ParapetThick = 30.f;

	/**
	 * HOW DEEP THE STONE FACE ALONG EACH SIDE HANGS BELOW THE DECK, and the
	 * one thing that makes a crossing read as a bridge from THIS camera.
	 *
	 * The window looks down on the island at about fifty degrees. At that
	 * angle a six-metre deck hides everything within two and a half metres
	 * under it, so the channel, the daylight and the piers are all real,
	 * measured, and completely invisible: what reaches the eye is the deck's
	 * own edge, a third of a metre of stone, and then water. Which is a road
	 * lying on a river, and reads as the causeway this was supposed to stop
	 * being.
	 *
	 * A spandrel is the wall a stone bridge carries along each side between
	 * its arches, and it is exactly the part of a bridge you CAN see from
	 * above. Built solid over each rank of piers and left open between them,
	 * it gives the side the alternating stone and shadow that says arches
	 * from any distance -- which is the whole of what a bridge looks like.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "400"))
	float Spandrel = 150.f;

	/**
	 * Tiles over which the dug channel eases back to the ordinary water level.
	 *
	 * Without it the river has a rectangular hole in it the width of the
	 * bridge, with a wall at each end.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "8"))
	int32 ChannelEase = 3;

	/** True while the level has named a deck; a level that has not draws none. */
	bool Any() const { return Deck != nullptr; }
};
