// Copyright interval.

#include "IntervalHud.h"
#include "IntervalTypes.h"
#include "IntervalMemory.h"

#include "Framework/Application/SlateApplication.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalGate.h"
#include "IntervalHand.h"
#include "Engine/Texture2D.h"
#include "IntervalGround.h"
#include "IntervalMenu.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/OverlaySlot.h"
#include "Components/Overlay.h"
#include "Components/SizeBox.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ProgressBar.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "IntervalLook.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

// §: NEVER `cond ? Bridge->GetFrame() : FIntervalFrame()`.
//
// It reads as a reference with a safe default and it is neither. The two arms
// of a conditional must have one type and one value category, so a reference
// on the left and a TEMPORARY on the right make the WHOLE expression a prvalue
// -- and binding it to `const FIntervalFrame&` then deep-copies the entire
// world: a TMap of every entity in sight, each one a TMap of strings. Every
// call. The `const&` on the left is what makes it look free.
//
// It cost the packaged client its frame rate. `AIntervalStructures::SownAt`
// does this and is called once per node from `Rebuild`, which runs on every
// chunk raised -- so walking into new country copied the world a few hundred
// times a chunk. A `sample` of the running game put 1,178 of 2,045 stacks
// inside the frame's copy constructor, under `SownAt`, under `RaiseChunk`.
//
// One shared empty frame, and both arms are real references.
// ONE NAME EACH, BECAUSE A UNITY BUILD HAS NO FILE SCOPE.
//
// `static` at file scope gives internal linkage in a translation unit of its
// own, and a unity build does not give it one: IntervalHand, IntervalHud and
// IntervalStructures each kept an empty frame under the same name, and the
// module stopped building the moment two of them were pasted together. Same
// fault as the colours and as `Round`, in the one place a scan for those two
// would not have looked.
static const FIntervalFrame GHudEmptyFrame;


// UNIQUE NAMES, BECAUSE A UNITY BUILD HAS NO FILE SCOPE.
//
// Unreal pastes several .cpp files into one translation unit, and an anonymous
// namespace in one of them is the SAME namespace as the anonymous namespace in
// the next. Five of these files called a colour Ink, three called one Quiet and
// one Ember, two an Oak and a Band, and the module stopped building the moment
// two of them landed in the same blob. Which files share a blob is UBT's
// business and changes between builds, so this is not a thing to fix by moving
// the collision somewhere else: the names are unique now and stay unique.
namespace
{
	// ---- THE PLATE ----
	//
	// The first cut of this was near-black and neutral grey, and it was called
	// what it was: "the grey color is so boring, the HUD is boring and ugly".
	// It was the colour of a debug overlay because that is what it grew out of.
	//
	// This world is oiled wood, tallow light and hammered brass. So: a panel is
	// dark stained OAK rather than charcoal, its edge is a brass band, the text
	// is tallow-lit PARCHMENT rather than white, and a slot is a recess cut
	// into the wood -- darker than the panel, not lighter, because a hole is
	// not a highlight. Nothing here is grey: every neutral carries a little
	// red and yellow in it, which is the whole difference between stone-cold
	// and candle-lit.
	const FLinearColor Parch(0.92f, 0.86f, 0.71f, 1.f);      // tallow on vellum
	const FLinearColor Faded(0.62f, 0.55f, 0.43f, 1.f);      // the same ink, older
	// THE GOLD THE CURSOR IS CAST IN -- see the note in IntervalGate.cpp.
	const FLinearColor Brass(0.839f, 0.659f, 0.290f, 1.f);
	const FLinearColor Lustre(0.988f, 0.910f, 0.659f, 1.f);      // the one bright metal
	// ---- INK AND GILT, NOT OAK ----
	//
	// The panels were a warm stained board with a brass band, and the whole
	// interface read as one particular twenty-year-old game -- which was
	// noticed: "I have a feeling that it's looking a little too much like
	// RuneScape."
	//
	// The LAYOUT is not the problem and is not changed: chat across the
	// bottom, the pack in a column at the right, a menu on the right click.
	// That arrangement is not a house style, it is what a click-to-act world
	// on a top-down view needs, and every game of this shape arrives at it.
	// What made it look borrowed was the SURFACE -- brown wood with a brass
	// edge is that game's own material.
	//
	// So the boards become ink: a cold near-black with a little blue in it,
	// the colour of a slate or a dark vellum, carrying one thin gold rule.
	// Gilt on ink is as medieval as wood and brass and belongs to nobody
	// else's window; and it lets the gold -- which is this project's own
	// colour, taken off the cursor -- do the work of saying where things are.
	const FLinearColor HudOak(0.038f, 0.040f, 0.052f, 0.90f);   // ink
	const FLinearColor OakLit(0.062f, 0.066f, 0.082f, 0.93f);// where the light falls
	const FLinearColor Recess(0.016f, 0.017f, 0.024f, 0.95f);// a socket cut in it
	const FLinearColor HudBand(0.52f, 0.40f, 0.17f, 0.85f);     // the one gold rule
	const FLinearColor Lit(0.86f, 0.62f, 0.28f, 0.22f);      // firelight on a hover
	const FLinearColor HudEmber(0.90f, 0.58f, 0.24f, 1.f);
	// THE PROJECT'S OWN COLOUR, taken off the cursor and used as the thread
	// through everything: the title on the gate, the rule round every panel,
	// the north point of the compass, and the name of whoever is speaking.
	const FLinearColor Gilt(0.839f, 0.659f, 0.290f, 1.f);

	// A PANEL IS A BOARD WITH A BAND ROUND IT, which is two borders and is the
	// cheapest thing that stops a rectangle reading as a debug window.
	/**
	 * A brush with the corners taken off. A little, not a lot.
	 *
	 * IT TAKES THE COLOUR TOO, and that is not tidiness. A square border is
	 * filled with its own `BrushColor`, which is what `SetBrushColor` sets; a
	 * ROUNDED one is filled by the shader from the BRUSH's `TintColor`, which
	 * `SetBrushColor` never touches and which defaults to white. So the moment
	 * the panels were rounded they all went white -- ink at nine-tenths alpha
	 * became white at nine-tenths alpha -- and the whole interface turned pale
	 * grey while the code still plainly said ink. Setting both is the fix, and
	 * putting both in one call is what stops it happening again.
	 */
	void HudRound(FSlateBrush& Brush, float Radius, const FLinearColor& Tint)
	{
		Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
		Brush.OutlineSettings.CornerRadii = FVector4(Radius, Radius, Radius, Radius);
		Brush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
		Brush.TintColor = FSlateColor(Tint);
	}

	UBorder* Board(UWidgetTree* Tree, UWidget* Inside, float Pad = 8.f)
	{
		UBorder* Edge = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Edge->SetBrushColor(HudBand);
		Edge->SetPadding(FMargin(2.f));
		// ROUNDED, BUT ONLY JUST. A square panel reads as a debug window and a
		// very round one reads as a phone; five pixels is the difference
		// between a rectangle and a made thing, and is what was asked for --
		// "a little more rounded in the edges. Not too much but a little".
		HudRound(Edge->Background, 6.f, HudBand);
		UBorder* Face = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Face->SetBrushColor(HudOak);
		HudRound(Face->Background, 5.f, HudOak);
		Face->SetPadding(FMargin(Pad, Pad * 0.75f, Pad, Pad * 0.75f));
		Face->AddChild(Inside);
		Edge->AddChild(Face);
		return Edge;
	}

	UTextBlock* Text(UWidgetTree* Tree, const FLinearColor& Tint, int32 Size)
	{
		UTextBlock* T = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		T->SetColorAndOpacity(FSlateColor(Tint));
		FSlateFontInfo Font = T->GetFont();
		Font.Size = Size;
		T->SetFont(Font);
		return T;
	}
}

// ---------------------------------------------------------------------------
// ONE SLOT.

namespace
{
	// The socket, and the sprite inside it. The inset keeps a blade off the
	// walls of its own recess, where it would read as cropped.
	constexpr float SlotSide = 52.f;
	constexpr float SlotArt = 44.f;

	// THE TWO NUMBERS THE WHOLE LAYOUT IS BUILT FROM. The pack is a narrow
	// column at the right and the chat is everything to the left of it, so
	// the chat has to know how wide the column is -- and only these say.
	constexpr int32 PackAcross = 3;
	constexpr float PackWide = PackAcross * (SlotSide + 4.f) + 18.f;
	// §6g: HOW MANY KINDS OF THING A COUNTER SHOWS AT ONCE.
	//
	// A vault holds up to the whole item table -- ninety-one words -- and a
	// grid of ninety-one is not something anybody reads. Thirty is five rows
	// of the pack's width: tall enough that a working citizen never fills it,
	// short enough to sit in the left margin without meeting the chat. When a
	// vault outgrows it the answer is a scroll, not a bigger wall.
	constexpr int32 VaultSlotsShown = 30;
	/** How many texels the minimap draws to a tile. See the note in Repaint. */
	constexpr int32 MapOver = 3;

	/**
	 * THE NINE CRAFTS, IN THE ORDER THEY ARE DRAWN, and the tool each one is
	 * practised with.
	 *
	 * The sprite is borrowed rather than drawn: every one of these items is
	 * already rendered for the pack, and a hatchet says "woodcraft" faster
	 * than the word does. The crafts themselves are the world's -- the bridge
	 * sends whatever the engine has -- so a founding with a tenth craft shows
	 * it with no icon and its name underneath, which is honest and not broken.
	 */
	const TArray<TPair<FString, FString>> CraftTools = {
		{ TEXT("woodcraft"),    TEXT("iron-hatchet") },
		{ TEXT("earthcraft"),   TEXT("iron-pickaxe") },
		{ TEXT("shorecraft"),   TEXT("rod") },
		{ TEXT("hearthcraft"),  TEXT("bread") },
		{ TEXT("prowess"),      TEXT("iron-sword") },
		{ TEXT("marksmanship"), TEXT("wooden-bow") },
		{ TEXT("sorcery"),      TEXT("bone-staff") },
		{ TEXT("mourning"),     TEXT("bones") },
		{ TEXT("wayfaring"),    TEXT("chart") },
	};
	constexpr float ChatDeep = 215.f;
	constexpr float ChatWide = 860.f;
	// The minimap, square, in the corner opposite the chat.
	constexpr float MapSide = 210.f;
	// The dark margin the compass letters stand on, between the picture and
	// the plate's gold rule.
	constexpr float MapEdge = 17.f;
}

namespace
{
	/**
	 * WHAT A STRETCH OF GROUND LOOKS LIKE FROM ABOVE.
	 *
	 * Keyed on the world's own word for the tile, matched loosely, because the
	 * names are the founding's and a new founding may invent more. Anything
	 * unrecognised comes out the colour of open country, which is what most
	 * of the island is and is never badly wrong.
	 */
	FColor GroundTint(const FString& Word)
	{
		auto Has = [&Word](const TCHAR* Bit)
		{
			return Word.Contains(Bit, ESearchCase::IgnoreCase);
		};
		if (Has(TEXT("water")) || Has(TEXT("sea")) || Has(TEXT("river"))
			|| Has(TEXT("lake")) || Has(TEXT("shoal")) || Has(TEXT("deep")))
		{
			return FColor(48, 78, 122);
		}
		if (Has(TEXT("sand")) || Has(TEXT("shore")) || Has(TEXT("dune"))
			|| Has(TEXT("beach")))
		{
			return FColor(176, 158, 118);
		}
		if (Has(TEXT("rock")) || Has(TEXT("stone")) || Has(TEXT("scree"))
			|| Has(TEXT("crag")) || Has(TEXT("ridge")))
		{
			return FColor(112, 110, 106);
		}
		if (Has(TEXT("snow")) || Has(TEXT("ice")))
		{
			return FColor(206, 210, 216);
		}
		if (Has(TEXT("marsh")) || Has(TEXT("bog")) || Has(TEXT("fen"))
			|| Has(TEXT("mire")))
		{
			return FColor(72, 84, 60);
		}
		if (Has(TEXT("wood")) || Has(TEXT("forest")) || Has(TEXT("grove")))
		{
			return FColor(52, 78, 46);
		}
		if (Has(TEXT("road")) || Has(TEXT("path")) || Has(TEXT("way")))
		{
			return FColor(140, 126, 102);
		}
		if (Has(TEXT("rough")) || Has(TEXT("heath")) || Has(TEXT("moor")))
		{
			return FColor(96, 100, 62);
		}
		return FColor(78, 104, 58);
	}

	/** What a thing standing on a tile is drawn as. */
	FColor ThingTint(const FString& Type)
	{
		auto Has = [&Type](const TCHAR* Bit)
		{
			return Type.Contains(Bit, ESearchCase::IgnoreCase);
		};
		if (Has(TEXT("wall")) || Has(TEXT("palisade")) || Has(TEXT("house"))
			|| Has(TEXT("fence")) || Has(TEXT("hedge")) || Has(TEXT("railing")))
		{
			return FColor(46, 42, 38);
		}
		if (Has(TEXT("stall")) || Has(TEXT("store")) || Has(TEXT("market"))
			|| Has(TEXT("smith")) || Has(TEXT("anvil")) || Has(TEXT("furnace"))
			|| Has(TEXT("vault")) || Has(TEXT("bank")))
		{
			return FColor(198, 148, 62);
		}
		if (Has(TEXT("keeper")) || Has(TEXT("crier")) || Has(TEXT("guard")))
		{
			return FColor(210, 206, 192);
		}
		if (Has(TEXT("tree")) || Has(TEXT("oak")) || Has(TEXT("grove")))
		{
			return FColor(40, 92, 42);
		}
		if (Has(TEXT("rock")) || Has(TEXT("seam")) || Has(TEXT("lode"))
			|| Has(TEXT("vent")) || Has(TEXT("rockfall")))
		{
			return FColor(150, 136, 108);
		}
		if (Has(TEXT("well")) || Has(TEXT("fountain")) || Has(TEXT("fishing"))
			|| Has(TEXT("eel")) || Has(TEXT("ferry")) || Has(TEXT("span")))
		{
			return FColor(96, 148, 190);
		}
		return FColor(150, 132, 104);
	}
}

TSharedRef<SWidget> UIntervalMapWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		// THE TEXTURE IS MADE LATER, in Repaint, where there is a world: a
		// widget's RebuildWidget also runs for the editor's own preview, and a
		// transient texture made there is made for nothing.
		Face = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		// SIZED BY A BOX, NOT BY THE BRUSH. `SetDesiredSizeOverride` on the
		// image is advice, and an auto-sizing canvas slot took the brush's own
		// idea instead -- the map came out thirty pixels square in the corner,
		// which is a smudge and not a map.
		// ---- AND A COMPASS ROUND IT ----
		//
		// A map that turns is only navigable if it says which way it is
		// pointing -- "we should probably add directions like north south west
		// east like a compass so it's easier to navigate the world". Four
		// letters ride on a circle OUTSIDE the face and are moved every frame,
		// so they swing round the rim as the camera turns and N always points
		// at the world's north however the picture is lying.
		//
		// OUTSIDE, and that is the second attempt. They sat just inside the
		// edge first, over the map itself, where they were illegible against
		// whatever terrain happened to be under them -- grey on green in a
		// meadow, grey on grey on a road -- and no colour fixes that, because
		// the background is different every second. Off the picture entirely,
		// on the dark surround, each letter has one constant backdrop and can
		// simply be read. It costs a margin round the map and buys a compass
		// that works.
		UCanvasPanel* Under = WidgetTree->ConstructWidget<UCanvasPanel>(
			UCanvasPanel::StaticClass());
		if (UCanvasPanelSlot* Whole = Under->AddChildToCanvas(Face))
		{
			Whole->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
			Whole->SetOffsets(FMargin(MapEdge));
		}
		static const TCHAR* const Letters[4] = { TEXT("N"), TEXT("E"), TEXT("S"), TEXT("W") };
		for (int32 Point = 0; Point < 4; ++Point)
		{
			UTextBlock* Mark = WidgetTree->ConstructWidget<UTextBlock>(
				UTextBlock::StaticClass());
			Mark->SetText(FText::FromString(Letters[Point]));
			// N IS THE LIT ONE. Three grey letters and one gold is the whole
			// difference between reading the rim and glancing at it.
			Mark->SetColorAndOpacity(FSlateColor(
				Point == 0 ? Gilt : FLinearColor(0.80f, 0.78f, 0.72f, 0.88f)));
			FSlateFontInfo Font = Mark->GetFont();
			Font.Size = Point == 0 ? 13 : 11;
			Font.TypefaceFontName = TEXT("Bold");
			Mark->SetFont(Font);
			// The letters must not eat a click meant for the ground beneath.
			Mark->SetVisibility(ESlateVisibility::HitTestInvisible);
			if (UCanvasPanelSlot* Where = Under->AddChildToCanvas(Mark))
			{
				Where->SetAutoSize(true);
				Where->SetAlignment(FVector2D(0.5f, 0.5f));
			}
			Points[Point] = Mark;
		}

		USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Size->SetWidthOverride(MapSide + 2.f * MapEdge);
		Size->SetHeightOverride(MapSide + 2.f * MapEdge);
		Size->AddChild(Under);
		UBorder* Plate = Board(WidgetTree, Size, 5.f);
		WidgetTree->RootWidget = Plate;
		// The plate must take a click, or the map is a picture.
		SetVisibility(ESlateVisibility::Visible);
	}
	return Super::RebuildWidget();
}

namespace
{
	/**
	 * The colour of a place you remember rather than a place you can see.
	 *
	 * Dimmed AND drained, not merely dimmed. Darkening alone made remembered
	 * meadow read as meadow at dusk, which is a thing the sky already does to
	 * the real map every evening -- two different facts drawn the same way.
	 * Pulling the colour towards grey as well says "this is not a sight" in a
	 * register the weather never uses.
	 */
	FColor Remembered(const FColor& Seen)
	{
		const float Grey = (Seen.R * 0.3f + Seen.G * 0.59f + Seen.B * 0.11f);
		auto Mix = [&](uint8 C)
		{
			return static_cast<uint8>(FMath::Clamp(
				(C * 0.45f + Grey * 0.55f) * 0.62f, 0.f, 255.f));
		};
		return FColor(Mix(Seen.R), Mix(Seen.G), Mix(Seen.B), 255);
	}
}

void UIntervalMapWidget::Repaint()
{
	// NOT `!Canvas`: the canvas is MADE below, on the first pass, and guarding
	// on it here meant the first pass returned before it could make anything
	// and every pass after it did the same. The map stayed the white of an
	// empty brush, which looks like a texture that failed to load rather than
	// a function that never ran.
	if (!Bridge)
	{
		return;
	}
	if (!Land)
	{
		TActorIterator<AIntervalGround> It(GetWorld());
		Land = It ? *It : nullptr;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		return;
	}
	if (Memory)
	{
		int32 Wide = 0, High = 0;
		Bridge->GetWorldSize(Wide, High);
		Memory->Bind(Wide, High, Bridge->GetPlayerId());
	}
	const int32 Side = Reach * 2 + 1;
	// SEVERAL TEXELS TO A TILE, AND THE REASON IS THE ZOOM.
	//
	// One texel per tile was right while the map showed a hundred and thirteen
	// of them: at under two screen pixels a tile nothing could be seen to have
	// a corner. Zoomed in to make a building clickable, the same picture is
	// four pixels a tile and every edge is a staircase -- "it looks so
	// pixelated, the pixelated look doesn't really fit well with this window".
	//
	// Drawing three texels to a tile and letting the sampler smooth costs a
	// blend across ONE texel, which is a third of a tile: a wall keeps its
	// corner and a diagonal road stops climbing stairs. Smoothing a one-texel
	// tile instead would have turned the wall into the smear the old note
	// warned about -- the note was right about its own picture and wrong about
	// this one.
	const int32 Pix = Side * MapOver;
	if (!Canvas)
	{
		Canvas = UTexture2D::CreateTransient(Pix, Pix, PF_B8G8R8A8);
		if (!Canvas)
		{
			return;
		}
		Canvas->Filter = TextureFilter::TF_Bilinear;
		Canvas->SRGB = true;
		Canvas->NeverStream = true;
		Canvas->UpdateResource();
		Pixels.SetNumUninitialized(Pix * Pix);
		UE_LOG(LogTemp, Log, TEXT("[interval] the map is %dx%d tiles, drawn %dx%d"),
			Side, Side, Pix, Pix);
		if (Face)
		{
			Face->SetBrushFromTexture(Canvas, false);
			Face->SetBrushSize(FVector2D(MapSide, MapSide));
		}
	}
	const TArray<FString>& Names = Bridge->GetTileNames();

	// 1. THE GROUND. A tile whose chunk has not been drawn is left dark --
	//    the map does not know what is there, and saying so is better than
	//    inventing a green field.
	// ---- THE MAP FACES THE WAY THE CITIZEN IS LOOKING ----
	//
	// Drawn north-up, a minimap is a map of the world; drawn camera-up, it is
	// a map of what is in front of you, and only the second is any use for
	// deciding where to click. The camera can be turned now, so the map turns
	// with it: "does the minimap rotate with the camera when the camera
	// rotates? I think it should."
	//
	// The camera's own yaw is the authority -- not the look asset's bearing
	// plus the spin, which is the same number arrived at by arithmetic that
	// can drift. Screen-up is the camera's forward flattened onto the ground;
	// screen-right is that turned a quarter.
	float Yaw = 0.f;
	if (const APlayerController* PC = GetOwningPlayer())
	{
		if (PC->PlayerCameraManager)
		{
			Yaw = PC->PlayerCameraManager->GetCameraRotation().Yaw;
		}
	}
	const float Rad = FMath::DegreesToRadians(Yaw);
	const float Cos = FMath::Cos(Rad);
	const float Sin = FMath::Sin(Rad);
	MapYaw = Yaw;

	// A TEXEL'S CENTRE, IN TILES. With three to a tile the middle one lands on
	// the tile's own centre and its neighbours a third either side, so a texel
	// that straddles a boundary honestly belongs to one side of it.
	auto TileOf = [&](int32 Col, int32 Row, int32& OutX, int32& OutY)
	{
		const float Across = (Col + 0.5f) / MapOver - (Reach + 0.5f);
		const float Down = (Row + 0.5f) / MapOver - (Reach + 0.5f);
		// forward * (-down) + right * across, with right = forward turned +90.
		const float Wx = Cos * (-Down) + (-Sin) * Across;
		const float Wy = Sin * (-Down) + (Cos) * Across;
		OutX = Frame.Me.X + FMath::RoundToInt(Wx);
		OutY = Frame.Me.Y + FMath::RoundToInt(Wy);
	};

	for (int32 Row = 0; Row < Pix; ++Row)
	{
		for (int32 Col = 0; Col < Pix; ++Col)
		{
			int32 TileX = 0, TileY = 0;
			TileOf(Col, Row, TileX, TileY);
			FColor Tint(18, 18, 20);
			// ---- SEEN NOW, SEEN ONCE, OR NEVER SEEN ----
			//
			// Three states and they are drawn as three. Ground in view is
			// drawn as it is. Ground this citizen walked past an hour ago is
			// drawn DIMMED -- it is a memory, and a memory that looked exactly
			// like a sight would be the window claiming to see round corners.
			// Ground never seen is left dark, which this map has always done
			// and is the honest drawing of how far a person can see.
			if (Land)
			{
				const uint8 Code = Land->CodeAtTile(TileX, TileY);
				if (Code != 255)
				{
					Tint = GroundTint(Names.IsValidIndex(Code) ? Names[Code] : FString());
					if (Memory) { Memory->Note(TileX, TileY, Code); }
				}
				else if (Memory)
				{
					const uint8 Was = Memory->Recall(TileX, TileY);
					if (Was != 255)
					{
						Tint = Remembered(GroundTint(
							Names.IsValidIndex(Was) ? Names[Was] : FString()));
					}
				}
			}
			// ---- AND THE PICTURE IS A DISC ----
			//
			// The compass rides a circle round the map, and a circle round a
			// SQUARE picture only clears it at the four cardinal points: with
			// the camera turned a half-quarter every letter landed on one of
			// the picture's own corners, over the terrain, which is where
			// they were before they were moved out and just as unreadable.
			// "I see the compass letters are still weirdly placed."
			//
			// Cutting the corners off the map fixes it once and for all --
			// every angle now has the same clear band of ink outside the
			// picture for a letter to sit on -- and it is also simply what a
			// minimap in this kind of game looks like.
			//
			// The corners are made TRANSPARENT rather than dark, so what
			// shows through is the board the plate is already made of.
			const float Ex = (Col + 0.5f) / MapOver - (Reach + 0.5f);
			const float Ey = (Row + 0.5f) / MapOver - (Reach + 0.5f);
			const float Edge = static_cast<float>(Reach) + 0.5f;
			Tint.A = (Ex * Ex + Ey * Ey) <= Edge * Edge ? 255 : 0;
			Pixels[Row * Pix + Col] = Tint;
		}
	}

	// WHERE THE WALK IS HEADED, drawn UNDER everything that stands on the
	// ground so a mark never hides a person. A ring, not a dot: the goal is
	// somewhere you are going to, not a thing that is there.
	//
	// It is the answer to walking blind. A click on this map asks for a walk
	// of up to fifty tiles, which is a minute of watching a citizen set off in
	// roughly the right direction and hoping.
	auto Ring = [&](int32 TileX, int32 TileY, const FColor& Tint)
	{
		const float Wx = static_cast<float>(TileX - Frame.Me.X);
		const float Wy = static_cast<float>(TileY - Frame.Me.Y);
		const float Across = -Sin * Wx + Cos * Wy;
		const float Down = -(Cos * Wx + Sin * Wy);
		// IN TILES, DRAWN IN TEXELS. The ring is two tiles out from the goal
		// whatever the picture is drawn at, so the radius is counted in tiles
		// and only the stepping is in texels -- an oversampled map would
		// otherwise shrink the ring to a smudge round the mark.
		const float Cx = (Across + Reach + 0.5f) * MapOver;
		const float Cy = (Down + Reach + 0.5f) * MapOver;
		// `Wide`, not `HudBand`: the palette's gold rule already owns that word.
		const int32 Wide = 2 * MapOver;
		for (int32 A = -Wide; A <= Wide; ++A)
		{
			for (int32 B = -Wide; B <= Wide; ++B)
			{
				if (FMath::Max(FMath::Abs(A), FMath::Abs(B)) < Wide - MapOver / 2)
				{
					continue;
				}
				const int32 Col = FMath::RoundToInt(Cx) + A;
				const int32 Row = FMath::RoundToInt(Cy) + B;
				if (Col < 0 || Row < 0 || Col >= Pix || Row >= Pix) { continue; }
				const float Ex = (Col + 0.5f) / MapOver - (Reach + 0.5f);
				const float Ey = (Row + 0.5f) / MapOver - (Reach + 0.5f);
				const float Lim = static_cast<float>(Reach) + 0.5f;
				if (Ex * Ex + Ey * Ey > Lim * Lim) { continue; }
				Pixels[Row * Pix + Col] = Tint;
			}
		}
	};
	if (Hand)
	{
		const FIntPoint Goal = Hand->GetRouteGoal();
		if (Goal.X != 0 || Goal.Y != 0)
		{
			Ring(Goal.X, Goal.Y, FColor(255, 108, 72));
		}
	}

	// 2. AND WHAT STANDS ON IT. Nodes first, then beasts, then people, so a
	//    citizen standing in a doorway is drawn and not the doorway.
	auto Mark = [&](int32 TileX, int32 TileY, const FColor& Tint)
	{
		// The inverse of the turn above: a world offset onto the picture.
		const float Wx = static_cast<float>(TileX - Frame.Me.X);
		const float Wy = static_cast<float>(TileY - Frame.Me.Y);
		const float Across = -Sin * Wx + Cos * Wy;
		const float Down = -(Cos * Wx + Sin * Wy);
		// Outside the disc there is no map, so there is nothing to mark on.
		const float Out = static_cast<float>(Reach) + 0.5f;
		if (Across * Across + Down * Down > Out * Out)
		{
			return;
		}
		// A MARK IS A TILE, NOT A TEXEL. Drawn as one texel it would be a
		// third of a citizen and the sampler would blend most of it away.
		const int32 Col0 = FMath::RoundToInt(
			(Across + Reach + 0.5f) * MapOver - MapOver * 0.5f);
		const int32 Row0 = FMath::RoundToInt(
			(Down + Reach + 0.5f) * MapOver - MapOver * 0.5f);
		for (int32 Dy = 0; Dy < MapOver; ++Dy)
		{
			for (int32 Dx = 0; Dx < MapOver; ++Dx)
			{
				const int32 Col = Col0 + Dx;
				const int32 Row = Row0 + Dy;
				if (Col >= 0 && Col < Pix && Row >= 0 && Row < Pix)
				{
					Pixels[Row * Pix + Col] = Tint;
				}
			}
		}
	};
	for (const TPair<FString, FIntervalEntity>& Node : Frame.Nodes)
	{
		// `Kind` is the entity's word for itself; the frame keeps no
		// separate `Type` on a node.
		Mark(Node.Value.X, Node.Value.Y, ThingTint(Node.Value.Kind));
	}
	for (const TPair<FString, FIntervalEntity>& Mob : Frame.Mobs)
	{
		Mark(Mob.Value.X, Mob.Value.Y, FColor(186, 72, 58));
	}
	for (const TPair<FString, FIntervalEntity>& Folk : Frame.Players)
	{
		Mark(Folk.Value.X, Folk.Value.Y, FColor(236, 236, 236));
	}
	// 3. AND THE CITIZEN, last and brightest, with a ring so they are findable
	//    on a busy map.
	Mark(Frame.Me.X, Frame.Me.Y, FColor(255, 232, 120));
	Mark(Frame.Me.X + 1, Frame.Me.Y, FColor(120, 96, 30));
	Mark(Frame.Me.X - 1, Frame.Me.Y, FColor(120, 96, 30));
	Mark(Frame.Me.X, Frame.Me.Y + 1, FColor(120, 96, 30));
	Mark(Frame.Me.X, Frame.Me.Y - 1, FColor(120, 96, 30));

	if (FTexturePlatformData* Data = Canvas->GetPlatformData())
	{
		if (Data->Mips.Num() > 0)
		{
			void* Where = Data->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
			FMemory::Memcpy(Where, Pixels.GetData(), Pixels.Num() * sizeof(FColor));
			Data->Mips[0].BulkData.Unlock();
			Canvas->UpdateResource();
		}
	}
}


// ---------------------------------------------------------------------------
// THE WHOLE ISLAND.

TSharedRef<SWidget> UIntervalWorldMapWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());

		// ONE PIXEL A TILE, shown at whatever size the island happens to be.
		// No scaling: an 896-wide island drawn at 896 pixels is a map whose
		// every pixel is a place you can stand, and a citizen counting tiles
		// off it is counting the real thing.
		Face = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		Over = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
		if (UCanvasPanelSlot* Whole = Over->AddChildToCanvas(Face))
		{
			Whole->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
			Whole->SetOffsets(FMargin(0.f));
		}
		// ---- EXACTLY ONE UNIT A TILE, AND SAID SO IN A BOX ----
		//
		// The canvas had no size of its own, so a Fill slot stretched it to
		// whatever the plate felt like -- about five hundred units for an
		// eight-hundred-and-ninety-six-tile island. The picture survived that
		// (an image scales) but the NAMES did not: a canvas slot is positioned
		// in canvas units, so Millbrook at tile 473 was drawn 473 units along
		// a canvas that was only 567 units wide, and every town sat well to
		// the south-east of where it is.
		//
		// Sized to the island exactly, canvas units ARE tile coordinates and
		// there is no arithmetic anywhere between the founding's numbers and
		// where a name lands. The box is filled in at paint time because the
		// island's size arrives with the world.
		Shape = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Shape->AddChild(Over);
		if (UVerticalBoxSlot* At = Column->AddChildToVerticalBox(Shape))
		{
			At->SetHorizontalAlignment(HAlign_Center);
		}

		// HOW MUCH OF IT YOU HAVE WALKED. It is the one number this map is
		// really about, and without it a mostly-dark island reads as a map
		// that failed to load rather than as a life that has only just begun.
		Caption = Text(WidgetTree, Faded, 12);
		Caption->SetJustification(ETextJustify::Center);
		if (UVerticalBoxSlot* At = Column->AddChildToVerticalBox(Caption))
		{
			At->SetPadding(FMargin(0.f, 7.f, 0.f, 0.f));
			At->SetHorizontalAlignment(HAlign_Fill);
		}
		WidgetTree->RootWidget = Column;
	}
	return Super::RebuildWidget();
}

void UIntervalWorldMapWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
	Super::NativeTick(Geometry, DeltaSeconds);
	if (!Bridge)
	{
		Bridge = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
		if (!Bridge) { return; }
	}
	// ON ITS OWN TERMS, not as a passenger of the bridge's. Fetching it inside
	// the `if (!Bridge)` block meant it was only ever looked up when the
	// bridge was missing -- and since the HUD hands the bridge over at
	// construction, that block never ran and the memory stayed null for ever.
	// The map opened, drew nothing, and looked like a panel with no content.
	if (!Memory)
	{
		Memory = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UIntervalMemorySubsystem>() : nullptr;
	}
	// ONLY WHILE IT IS OPEN, and only every second or so. Repainting half a
	// million pixels every frame to redraw a map nobody is looking at is the
	// kind of cost that does not show up until the window is doing something
	// else as well.
	const double Now = FPlatformTime::Seconds();
	if (Now - PaintedAt < 1.0)
	{
		return;
	}
	PaintedAt = Now;
	Repaint();
}

FReply UIntervalWorldMapWidget::NativeOnMouseButtonDown(const FGeometry& Geometry,
	const FPointerEvent& Event)
{
	// ---- A CLICK ON THE ISLAND IS A JOURNEY ----
	//
	// This is what a world map is FOR. The minimap can ask for a walk as far
	// as it draws, which is fifty-odd tiles; anywhere actually worth going --
	// the timber town, the forge, the far coast -- is several times that, and
	// crossing the island by minimap is a dozen clicks in a row with a stall
	// to recover from in the middle of each.
	//
	// And it is the one map with no rotation in it. The minimap turns with the
	// camera, so every click on it has to be read back through a yaw that is
	// still interpolating while the citizen walks -- which is a small error
	// that becomes a large one over fifty tiles, and is why a walk aimed due
	// north kept setting off north-east. Here the canvas is sized to the
	// island exactly, so a pixel IS a tile, north is up, and there is no
	// arithmetic between the click and the destination at all.
	if (!Hand || !Memory || !Memory->IsBound() || !Face)
	{
		return FReply::Unhandled();
	}
	const FGeometry& Face_ = Face->GetCachedGeometry();
	const FVector2D Local = Face_.AbsoluteToLocal(Event.GetScreenSpacePosition());
	const FVector2D Size = Face_.GetLocalSize();
	if (Size.X <= 0.f || Size.Y <= 0.f)
	{
		return FReply::Unhandled();
	}
	const int32 WantX = FMath::Clamp(
		FMath::FloorToInt(Local.X / Size.X * Memory->GetWide()), 0, Memory->GetWide() - 1);
	const int32 WantY = FMath::Clamp(
		FMath::FloorToInt(Local.Y / Size.Y * Memory->GetHigh()), 0, Memory->GetHigh() - 1);
	Hand->WalkRoute(WantX, WantY);
	return FReply::Handled();
}

void UIntervalWorldMapWidget::Repaint()
{
	if (!Memory || !Memory->IsBound() || !Face)
	{
		return;
	}
	const int32 Wide = Memory->GetWide();
	const int32 High = Memory->GetHigh();
	if (!Canvas)
	{
		Canvas = UTexture2D::CreateTransient(Wide, High, PF_B8G8R8A8);
		if (!Canvas)
		{
			return;
		}
		Canvas->Filter = TextureFilter::TF_Nearest;
		Canvas->SRGB = true;
		Canvas->NeverStream = true;
		Canvas->UpdateResource();
		Pixels.SetNumUninitialized(Wide * High);
		Face->SetBrushFromTexture(Canvas, false);
		Face->SetDesiredSizeOverride(FVector2D(Wide, High));
		if (Shape)
		{
			Shape->SetWidthOverride(Wide);
			Shape->SetHeightOverride(High);
		}
	}

	const TArray<FString>& Names = Bridge->GetTileNames();
	for (int32 Y = 0; Y < High; ++Y)
	{
		for (int32 X = 0; X < Wide; ++X)
		{
			const uint8 Code = Memory->Recall(X, Y);
			// NEVER SEEN IS NEARLY BLACK AND NOT BLANK. A hole in a map should
			// still read as part of the island rather than as a hole in the
			// window, so unwalked ground is the colour of the board it sits on
			// with the faintest lift.
			Pixels[Y * Wide + X] = Code == 255
				? FColor(13, 14, 18)
				: GroundTint(Names.IsValidIndex(Code) ? Names[Code] : FString());
		}
	}

	// AND WHERE YOU ARE, in the one colour nothing else on this map uses.
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (Frame.bHasMe)
	{
		for (int32 D = -2; D <= 2; ++D)
		{
			auto Dot = [&](int32 X, int32 Y)
			{
				if (X >= 0 && Y >= 0 && X < Wide && Y < High)
				{
					Pixels[Y * Wide + X] = FColor(255, 214, 96);
				}
			};
			Dot(Frame.Me.X + D, Frame.Me.Y);
			Dot(Frame.Me.X, Frame.Me.Y + D);
		}
	}

	if (FTexturePlatformData* Data = Canvas->GetPlatformData())
	{
		if (Data->Mips.Num() > 0)
		{
			void* Raw = Data->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
			FMemory::Memcpy(Raw, Pixels.GetData(), Pixels.Num() * sizeof(FColor));
			Data->Mips[0].BulkData.Unlock();
			Canvas->UpdateResource();
		}
	}

	// ---- THE NAMES OF THE PLACES YOU HAVE BEEN ----
	//
	// The founding lists every settlement on the island and the window has had
	// that list since the day it opened. Writing the names on means the map
	// answers "where is Thornbury" and not merely "what shape is the coast" --
	// and only the ones whose ground this citizen has actually stood on are
	// written, so the map never names somewhere you have not found.
	if (Over && Signs.Num() == 0)
	{
		for (const FIntervalSettlement& Town : Bridge->GetSettlements())
		{
			UTextBlock* Sign = Text(WidgetTree, Gilt, 10);
			Sign->SetText(FText::FromString(Town.Name));
			Sign->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* At = Over->AddChildToCanvas(Sign))
			{
				At->SetAutoSize(true);
				At->SetAlignment(FVector2D(0.5f, 0.5f));
				At->SetPosition(FVector2D(Town.X, Town.Y));
			}
			Signs.Add(Sign);
		}
	}
	const TArray<FIntervalSettlement>& Towns = Bridge->GetSettlements();
	for (int32 i = 0; i < Signs.Num() && i < Towns.Num(); ++i)
	{
		if (Signs[i])
		{
			Signs[i]->SetVisibility(Memory->Recall(Towns[i].X, Towns[i].Y) != 255
				? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
	}

	// WHERE THE PICTURE IS, SAID OUT LOUD.
	//
	// Only for the harness, and it earns its line. Everything that aims at
	// this window from outside has so far had to REDERIVE a widget's rectangle
	// from the chain of paddings that produced it -- two borders, a size box,
	// a viewport scale -- and every one of those numbers has moved at least
	// once this session. A rectangle that the widget itself reports cannot
	// drift from the widget, and finding it by looking for a colour in a
	// screenshot fails the moment the world happens to contain that colour,
	// which it does.
	if (Face)
	{
		const FGeometry& Seen_ = Face->GetCachedGeometry();
		const FVector2D Corner = Seen_.GetAbsolutePosition();
		const FVector2D Span = Seen_.GetAbsoluteSize();
		UE_LOG(LogTemp, Log, TEXT("[isle] face %0.1f %0.1f %0.1f %0.1f tiles %d %d"),
			Corner.X, Corner.Y, Span.X, Span.Y, Wide, High);
	}

	// ---- AND WHERE THE CITIZEN IS HEADED ----
	//
	// A click on a map sends somebody walking for a minute, and until now
	// nothing on screen said where they had asked to go -- "otherwise you're
	// walking blind it feels like". The route knows its own goal; it only
	// needed drawing. A ring rather than a dot, because the goal is a place
	// you are going TO and a dot is a thing that is already there.
	if (Hand)
	{
		const FIntPoint Goal = Hand->GetRouteGoal();
		if (Goal.X != 0 || Goal.Y != 0)
		{
			for (int32 D = -3; D <= 3; ++D)
			{
				auto Ring = [&](int32 X, int32 Y)
				{
					if (X >= 0 && Y >= 0 && X < Wide && Y < High)
					{
						Pixels[Y * Wide + X] = FColor(255, 108, 72);
					}
				};
				if (FMath::Abs(D) == 3)
				{
					for (int32 E = -3; E <= 3; ++E)
					{
						Ring(Goal.X + D, Goal.Y + E);
						Ring(Goal.X + E, Goal.Y + D);
					}
				}
			}
		}
	}

	if (Caption)
	{
		const int32 Seen = Memory->GetSeenCount();
		const int32 All = FMath::Max(Wide * High, 1);
		Caption->SetText(FText::FromString(FString::Printf(
			TEXT("%d of %d tiles walked  --  %.1f%% of the island"),
			Seen, All, 100.f * Seen / All)));
	}
}

void UIntervalMapWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
	Super::NativeTick(Geometry, DeltaSeconds);
	if (!Bridge)
	{
		// WIRED HERE IF NOWHERE ELSE. This widget is built inside
		// `AddToViewport`, which runs before the actor that owns it has handed
		// over anything -- so on a first construction it had a null bridge and
		// quietly painted nothing at all, which on screen is a plain white
		// square where the map should be.
		Bridge = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
		if (!Hand)
		{
			TActorIterator<AIntervalHand> It(GetWorld());
			Hand = It ? *It : nullptr;
		}
		if (!Bridge)
		{
			return;
		}
	}
	// The remembered map, on its own terms and not as a passenger of the
	// bridge's -- see the note in the world map's tick.
	if (!Memory)
	{
		Memory = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UIntervalMemorySubsystem>() : nullptr;
	}
	// ONCE AN INTERVAL. The world only changes that often, and repainting a
	// hundred and thirteen tiles a side every frame is a lot of work to draw
	// the same map.
	// WHERE THE FOUR LETTERS SIT, every frame and not every tick: the camera
	// turns smoothly and a compass that stepped once a second would read as a
	// broken one.
	float Yaw = 0.f;
	if (const APlayerController* PC = GetOwningPlayer())
	{
		if (PC->PlayerCameraManager)
		{
			Yaw = PC->PlayerCameraManager->GetCameraRotation().Yaw;
		}
	}
	{
		const float Rad = FMath::DegreesToRadians(Yaw);
		const float Cos = FMath::Cos(Rad);
		const float Sin = FMath::Sin(Rad);
		// North is -Y in this world -- the north pass is row 174 and the south
		// one row 317 -- east is +X, and the rest follow round.
		const FVector2D Ways[4] = {
			FVector2D(0.f, -1.f), FVector2D(1.f, 0.f),
			FVector2D(0.f, 1.f), FVector2D(-1.f, 0.f) };
		// Just outside the disc, on the board, at every angle alike.
		const float Ring = MapSide * 0.5f + MapEdge * 0.55f;
		const float Middle = MapSide * 0.5f + MapEdge;
		for (int32 Point = 0; Point < 4; ++Point)
		{
			if (!Points[Point])
			{
				continue;
			}
			// The same turn the picture is drawn with, read the other way.
			const FVector2D& Way = Ways[Point];
			const float Across = -Sin * Way.X + Cos * Way.Y;
			const float Down = -(Cos * Way.X + Sin * Way.Y);
			if (UCanvasPanelSlot* Where = Cast<UCanvasPanelSlot>(Points[Point]->Slot))
			{
				Where->SetPosition(FVector2D(
					Middle + Across * Ring,
					Middle + Down * Ring));
			}
		}
	}

	// THE PICTURE ITSELF repaints on a new tick OR on a turn of the camera.
	// Only the first was ever true before there was anything to turn, and a
	// map that waited a whole second to follow the camera lags visibly behind
	// its own compass.
	const FIntervalFrame& Frame = Bridge->GetFrame();
	const bool bTurned = FMath::Abs(FRotator::NormalizeAxis(Yaw - MapYaw)) > 1.5f;
	if (Frame.Tick == LastPainted && !bTurned)
	{
		return;
	}
	LastPainted = Frame.Tick;
	Repaint();
}

FReply UIntervalMapWidget::NativeOnMouseButtonDown(const FGeometry& Geometry,
	const FPointerEvent& Event)
{
	// A CLICK ON THE MAP IS A WALK, and a long one: this is the whole point.
	//
	// The picture is centred on the citizen, so the tile is read straight off
	// where in it the click landed. Nothing else is offered -- a right click
	// on the map does not open the menu, because a thing fifty tiles away
	// cannot be acted on and a menu that offered to would be a lie.
	if (!Hand || !Bridge)
	{
		return FReply::Unhandled();
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		return FReply::Unhandled();
	}
	// THE IMAGE'S GEOMETRY, NOT THE PLATE'S.
	//
	// The click arrives with the geometry of this widget's ROOT, which is the
	// bordered plate the map sits in -- so the padding and the band count as
	// map, and every click is read a few tiles off in both directions. Over a
	// hundred and thirteen tiles that is a walk to the wrong place entirely:
	// asking for five tiles north-east produced a route twenty-six east and
	// nine north. The face knows its own rectangle; ask that.
	const FGeometry& Face_ = Face ? Face->GetCachedGeometry() : Geometry;
	const FVector2D Local = Face_.AbsoluteToLocal(Event.GetScreenSpacePosition());
	const FVector2D Size = Face_.GetLocalSize();
	if (Size.X <= 0.f || Size.Y <= 0.f)
	{
		return FReply::Unhandled();
	}
	const int32 Side = Reach * 2 + 1;
	const int32 Col = FMath::Clamp(
		FMath::FloorToInt(Local.X / Size.X * Side), 0, Side - 1);
	const int32 Row = FMath::Clamp(
		FMath::FloorToInt(Local.Y / Size.Y * Side), 0, Side - 1);
	// ROUTE, not walk: see the note on WalkRoute. A map click that stops at
	// the first wall is a map click that does not work.
	// THROUGH THE SAME TURN THE PICTURE WAS DRAWN WITH, or a click on a map
	// that has been rotated walks somewhere else entirely.
	const float RadC = FMath::DegreesToRadians(MapYaw);
	const float CosC = FMath::Cos(RadC);
	const float SinC = FMath::Sin(RadC);
	const float AcrossC = static_cast<float>(Col - Reach);
	const float DownC = static_cast<float>(Row - Reach);
	const int32 WantX = Frame.Me.X
		+ FMath::RoundToInt(CosC * (-DownC) + (-SinC) * AcrossC);
	const int32 WantY = Frame.Me.Y
		+ FMath::RoundToInt(SinC * (-DownC) + (CosC) * AcrossC);
	UE_LOG(LogTemp, Log,
		TEXT("[interval] map click at %.1f,%.1f of %.0fx%.0f -> tile %d,%d"),
		Local.X, Local.Y, Size.X, Size.Y, WantX, WantY);
	Hand->WalkRoute(WantX, WantY);
	return FReply::Handled();
}

TSharedRef<SWidget> UIntervalTabWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UButton* Hit_ = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		FButtonStyle Style = Hit_->GetStyle();
		Style.Normal.TintColor = FSlateColor(Recess);
		Style.Hovered.TintColor = FSlateColor(Lit);
		Style.Pressed.TintColor = FSlateColor(Brass * 0.4f);
		Hit_->SetStyle(Style);
		Hit_->OnClicked.AddDynamic(this, &UIntervalTabWidget::Hit);

		// HEIGHT ONLY. The width comes from the column it is in -- see the
		// note where the tabs are built -- so that three tabs and three
		// columns of slots line up rather than nearly lining up.
		USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Size->SetHeightOverride(42.f);

		Mark = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		// THE ICONS ARE ITEM SPRITES, and deliberately so. A helm stands for
		// what is worn, a sigil for the citizen, a chart for the book, a
		// charter for the island -- all four already rendered by
		// `Tools/icons.py`, all four in the same hand as everything else in
		// the pack. Drawing four more in a different style would only make the
		// row look assembled.
		if (UTexture2D* Art = UIntervalSlotWidget::IconFor(Icon))
		{
			Mark->SetBrushFromTexture(Art, false);
			Mark->SetDesiredSizeOverride(FVector2D(30.f, 30.f));
		}
		Size->AddChild(Mark);
		if (UButtonSlot* Slot = Cast<UButtonSlot>(Hit_->AddChild(Size)))
		{
			Slot->SetPadding(FMargin(0.f));
			Slot->SetHorizontalAlignment(HAlign_Fill);
			Slot->SetVerticalAlignment(VAlign_Fill);
		}
		// The world's key, spoken. See IntervalName::Spoken.
		SetToolTipText(FText::FromString(IntervalName::Spoken(Title)));
		WidgetTree->RootWidget = Hit_;
	}
	return Super::RebuildWidget();
}

void UIntervalTabWidget::Light(bool bOpen)
{
	if (UButton* Button = Cast<UButton>(GetRootWidget()))
	{
		FButtonStyle Style = Button->GetStyle();
		// THE OPEN ONE IS LIT. Without it the sheet above looks like it
		// belongs to nothing and a second click to close it is a guess.
		Style.Normal.TintColor = FSlateColor(bOpen ? HudBand : Recess);
		Button->SetStyle(Style);
	}
}

void UIntervalTabWidget::Hit()
{
	if (Owner)
	{
		Owner->OpenSheet(Which);
	}
}

// ---------------------------------------------------------------------------

TSharedRef<SWidget> UIntervalSpellRow::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UButton* Hit_ = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		FButtonStyle Style = Hit_->GetStyle();
		Style.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
		Style.Hovered.TintColor = FSlateColor(Lit);
		Style.Pressed.TintColor = FSlateColor(Brass * 0.4f);
		Hit_->SetStyle(Style);
		Hit_->OnClicked.AddDynamic(this, &UIntervalSpellRow::Speak);

		UTextBlock* Word = Text(WidgetTree, bKnown ? Parch : Faded, 12);
		Word->SetText(FText::FromString(Label.IsEmpty() ? Spell : Label));
		if (UButtonSlot* Slot = Cast<UButtonSlot>(Hit_->AddChild(Word)))
		{
			Slot->SetPadding(FMargin(6.f, 2.f, 10.f, 2.f));
			Slot->SetHorizontalAlignment(HAlign_Left);
		}
		WidgetTree->RootWidget = Hit_;
	}
	return Super::RebuildWidget();
}

TSharedRef<SWidget> UIntervalWornRow::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UButton* Hit_ = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		FButtonStyle Style = Hit_->GetStyle();
		Style.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
		Style.Hovered.TintColor = FSlateColor(Lit);
		Style.Pressed.TintColor = FSlateColor(Brass * 0.4f);
		Hit_->SetStyle(Style);
		Hit_->OnClicked.AddDynamic(this, &UIntervalWornRow::Take);

		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
			UHorizontalBox::StaticClass());
		UTextBlock* Left = Text(WidgetTree, Brass, 11);
		Left->SetText(FText::FromString(Gear));
		if (USizeBox* Width = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass()))
		{
			// NARROWER THAN THE CRAFTS' COLUMN. That one is 104 because
			// `marksmanship` is eleven letters; the slots are `offhand` at
			// worst, and 104 pushed `iron-shield` off the right-hand edge of
			// a sheet that is only as wide as the pack.
			Width->SetWidthOverride(62.f);
			Width->AddChild(Left);
			Row->AddChildToHorizontalBox(Width);
		}
		UTextBlock* Right = Text(WidgetTree, Item.IsEmpty() ? Faded : Parch, 11);
		Right->SetText(FText::FromString(
			Item.IsEmpty() ? TEXT("--") : IntervalName::Spoken(Item)));
		Row->AddChildToHorizontalBox(Right);
		if (UButtonSlot* Slot = Cast<UButtonSlot>(Hit_->AddChild(Row)))
		{
			Slot->SetPadding(FMargin(0.f, 1.f, 0.f, 1.f));
			Slot->SetHorizontalAlignment(HAlign_Left);
		}
		WidgetTree->RootWidget = Hit_;
	}
	return Super::RebuildWidget();
}

void UIntervalWornRow::Take()
{
	// AN EMPTY SLOT IS NOT A BUTTON. The row is still drawn, because a sheet
	// that lists only what is on cannot be read as "and these are the places
	// something could be"; it simply does nothing when pressed.
	if (Hand && !Item.IsEmpty() && !Gear.IsEmpty())
	{
		Hand->Unwield(Gear);
	}
}

void UIntervalSpellRow::Speak()
{
	// IT IS SPOKEN WHETHER OR NOT THIS WINDOW THINKS IT CAN BE. A book the
	// citizen does not carry, a spell they have not learned, a target that is
	// not there -- all of those are the world's to refuse, and it says so in
	// the feed. A greyed-out row that cannot be clicked would be this window
	// keeping a second copy of the rules.
	if (!Hand)
	{
		return;
	}
	if (Verb == TEXT("invoke"))
	{
		Hand->Invoke();
		return;
	}
	// NOT EVERY LINE IN A SHEET IS A DEED EITHER. The daylight line asks the
	// world for nothing at all; it is this window deciding what to draw.
	if (Verb == TEXT("daylight"))
	{
		if (Hud) { Hud->TurnTheSun(); }
		return;
	}
	// A DEED ABOUT THE CITIZEN THEMSELVES. Some of them want a choice as well
	// -- which calling, how long a stint -- and those open the ordinary menu
	// rather than growing a second kind of list inside the sheet.
	if (!Verb.IsEmpty() && !On.Id.IsEmpty())
	{
		if (Hand->ChoicesFor(On, Verb).Num() > 0)
		{
			Hand->UiTookTheClick = 2;
			Hand->OnOptions.Broadcast({ On });
			return;
		}
		Hand->ActOnWith(Verb, On, FString());
		return;
	}
	Hand->Cast(Spell);
}

// ---------------------------------------------------------------------------

TSharedRef<SWidget> UIntervalSlotWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		// A SLOT IS A SOCKET CUT IN THE BOARD, and it holds a thing or it is
		// empty. NOTHING IS WRITTEN IN IT: "no '11 of 12 free' or anything like
		// that. Just the slots, either empty or with the item sprite sitting in
		// the slot if there is an item there." The name belongs on the hover,
		// where it is asked for, and nowhere else -- a grid with a word in every
		// cell is a list with lines round it.
		UButton* Hit = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		FButtonStyle Style = Hit->GetStyle();
		Style.Normal.TintColor = FSlateColor(Recess);
		Style.Hovered.TintColor = FSlateColor(Lit);
		Style.Pressed.TintColor = FSlateColor(Brass * 0.4f);
		Hit->SetStyle(Style);
		Hit->OnClicked.AddDynamic(this, &UIntervalSlotWidget::Picked);

		USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Size->SetWidthOverride(SlotSide);
		Size->SetHeightOverride(SlotSide);

		UOverlay* Stack = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());

		// THE SPRITE ITSELF, which is the whole point of a slot.
		//
		// This drew the item's INITIAL in brass while there was no art -- a
		// deliberate stand-in, and it read as one: "I see arrows is just an A.
		// It has to look like arrows." There are now a hundred and thirty
		// sprites, rendered from the items' own meshes by `Tools/icons.py`, so
		// the sword in the pack is the same sword that is on the citizen's
		// back. See `IconFor` below for where they come from.
		Sprite = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		Sprite->SetVisibility(ESlateVisibility::Collapsed);
		if (UOverlaySlot* Cell_ = Stack->AddChildToOverlay(Sprite))
		{
			Cell_->SetHorizontalAlignment(HAlign_Fill);
			Cell_->SetVerticalAlignment(VAlign_Fill);
			// A LITTLE INSET, so a sprite does not touch the walls of its
			// socket -- a blade running into the corner of the recess reads
			// as a blade that has been cropped.
			Cell_->SetPadding(FMargin((SlotSide - SlotArt) * 0.5f));
		}
		// AND THE LETTER, KEPT, for the one case it is still right for: an
		// item whose sprite is missing. A blank slot that holds something is a
		// worse lie than a letter, and it is how a new word in the world
		// announces that its art has not been made yet.
		Name = Text(WidgetTree, Brass, 20);
		Name->SetJustification(ETextJustify::Center);
		if (UOverlaySlot* Cell_ = Stack->AddChildToOverlay(Name))
		{
			Cell_->SetHorizontalAlignment(HAlign_Center);
			Cell_->SetVerticalAlignment(VAlign_Center);
		}
		// THE COUNT, TOP RIGHT, AND OUT OF THE WAY OF THE ART.
		//
		// It sat bottom right, over the item, and the item lost by it: "the
		// arrow amount number kind of isn't as legible as it could be... makes
		// the arrows not seem as good as they can be, because they're on the
		// arrow heads." Both halves of that are true and they have different
		// causes, so both are fixed here.
		//
		// WHERE. Top RIGHT. It went to the top LEFT first and still sat on the
		// arrowheads -- "it still is touching the arrows and it feels wrong for
		// some reason". It does, and for a reason worth writing down: the
		// sprites are rendered from one fixed three-quarter angle that lays
		// every long thing along the same diagonal, running up to the right, so
		// the top-left corner is exactly where the HEAD of a long item lands
		// and is the one corner that is never free. The two corners that are
		// free in every icon are the top right and the bottom left.
		//
		// LEGIBILITY. A pale number on a sprite that might be pale is a number
		// that disappears; it now carries a hard black shadow, which is what
		// makes small text hold up over arbitrary art.
		// THE COUNT IN THE BRIGHT METAL, so a stack reads at a glance
		// against any sprite under it. See the gold's note in the gate.
		Count = Text(WidgetTree, Lustre, 10);
		Count->SetShadowOffset(FVector2D(1.f, 1.f));
		Count->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.85f));
		if (UOverlaySlot* Cell_ = Stack->AddChildToOverlay(Count))
		{
			Cell_->SetHorizontalAlignment(HAlign_Right);
			Cell_->SetVerticalAlignment(VAlign_Top);
			Cell_->SetPadding(FMargin(0.f, 1.f, 4.f, 0.f));
		}
		Size->AddChild(Stack);
		if (UButtonSlot* Slot = Cast<UButtonSlot>(Hit->AddChild(Size)))
		{
			Slot->SetPadding(FMargin(0.f));
			Slot->SetHorizontalAlignment(HAlign_Fill);
			Slot->SetVerticalAlignment(VAlign_Fill);
		}
		WidgetTree->RootWidget = Hit;
	}
	return Super::RebuildWidget();
}

UTexture2D* UIntervalSlotWidget::IconFor(const FString& Which)
{
	// BY NAME, AND CACHED, AND NEVER RE-ASKED.
	//
	// `Tools/import_icons.py` puts one texture per item in /Game/Interval/Icons
	// under the item's own name with the hyphens turned to underscores, which
	// is the only spelling an Unreal asset name allows. So the lookup needs no
	// table: the world says `gold-helm` and the texture is `gold_helm`.
	//
	// The cache holds MISSES as well as hits -- a null entry for an item with
	// no art. Without that, every frame of every slot holding an unrendered
	// item is a failed synchronous package load, which is the kind of thing
	// that does not show up until a citizen picks up something new and the
	// window starts stuttering once a second for no visible reason.
	// AND THE CACHE IS ROOTED, OR IT IS A LIST OF DANGLING POINTERS.
	//
	// This was a `static TMap<FString, TObjectPtr<UTexture2D>>`, and a static
	// local is INVISIBLE TO THE COLLECTOR: nothing traces it, so a TObjectPtr
	// in one roots nothing. The textures loaded, the map kept them, the next
	// full collection freed every one of them, and the map went on handing out
	// the addresses. `SetBrushFromTexture` then read freed memory.
	//
	// It crashed on CROSSING, every time, because crossing out of Nought tears
	// down a world and that forces the full collection this had survived until
	// then. The report is unmistakable once seen: EXC_BAD_ACCESS at
	// 0xdddddddddddd..., which is Unreal's own poison fill for freed memory,
	// inside FSlateRHIRenderer::CanRenderResource under the HUD's tick.
	//
	// `AddToRoot` is the right answer rather than a UPROPERTY on some owner:
	// there are a hundred and thirty items, the set is bounded and known at
	// build time, and the cache is deliberately never re-asked. These should
	// live as long as the process, and now they say so.
	static TMap<FString, TObjectPtr<UTexture2D>> Known;
	if (const TObjectPtr<UTexture2D>* Found = Known.Find(Which))
	{
		return Found->Get();
	}
	// AND A MINTED KEY IS FOLDED TO ITS WORD FIRST. A hood, a fall stone and
	// an attuned chart all carry a hash or a place after a colon, which is not
	// a legal asset name and so never matched anything: the wardrobe folded
	// them and drew them on the citizen, and this did not, so the one person
	// who had earned a hood wore it and had an empty square in their pack.
	const FString Asset = IntervalName::Row(Which).Replace(TEXT("-"), TEXT("_"));
	const FString Path = FString::Printf(
		TEXT("/Game/Interval/Icons/%s.%s"), *Asset, *Asset);
	UTexture2D* Loaded = LoadObject<UTexture2D>(nullptr, *Path);
	if (Loaded)
	{
		// held against collection for the life of the process: see above
		Loaded->AddToRoot();
	}
	Known.Add(Which, Loaded);
	if (!Loaded)
	{
		UE_LOG(LogTemp, Verbose, TEXT("[interval] no sprite for %s"), *Which);
	}
	return Loaded;
}

void UIntervalSlotWidget::Show(const FString& InItem, int32 InQty)
{
	Item = InItem;
	Qty = InQty;
	UTexture2D* Icon = Item.IsEmpty() ? nullptr : IconFor(Item);
	if (Sprite)
	{
		if (Icon)
		{
			// MATCH SIZE OFF, AND THE SIZE SET BY HAND.
			//
			// `SetBrushFromTexture(Icon, true)` takes the TEXTURE'S size as the
			// brush size, which is 128 -- and a 128-pixel brush in a 52-pixel
			// socket is not scaled down, it is cropped. The slot showed the
			// top-left corner of every sprite, which for the arrows was three
			// arrowheads and no shafts and looked like a sprite drawn badly
			// rather than a sprite drawn at the wrong size.
			Sprite->SetBrushFromTexture(Icon, false);
			Sprite->SetDesiredSizeOverride(FVector2D(SlotArt, SlotArt));
		}
		Sprite->SetVisibility(Icon ? ESlateVisibility::HitTestInvisible
		                           : ESlateVisibility::Collapsed);
	}
	if (Name)
	{
		// The letter only when there is no sprite: see the note in
		// RebuildWidget. An empty slot shows neither.
		Name->SetText((Item.IsEmpty() || Icon) ? FText::GetEmpty()
			: FText::FromString(Item.Left(1).ToUpper()));
	}
	// AND NO TOOLTIP.
	//
	// The name used to live on the hover, which was right when the slot had no
	// other way of saying what it held. It has one now: a right click names
	// the thing at the top of its own menu and again on every line. With both,
	// the tooltip appeared over the menu it duplicated -- "arrows" in a white
	// box sitting on top of "drop arrows" -- which reads as a fault rather
	// than as a label. One name is enough.
	if (Count)
	{
		// A COUNT ONLY WHERE THERE IS ONE TO SHOW. `×1` on every slot is noise,
		// and the number is the thing a citizen is actually reading when they
		// glance down mid-swing.
		Count->SetText(Qty > 1 ? FText::FromString(FString::Printf(TEXT("%d"), Qty))
		                       : FText::GetEmpty());
	}
}

FReply UIntervalSlotWidget::NativeOnMouseButtonDown(const FGeometry& Geometry,
	const FPointerEvent& Event)
{
	// RIGHT CLICK ON A THING IN THE PACK, which is the other half of the
	// arrangement the world already has: left does the obvious thing, right
	// says everything. A button's OnClicked is a LEFT click and nothing else,
	// so until now the pack had only the obvious thing.
	if (Event.GetEffectingButton() != EKeys::RightMouseButton
		|| Item.IsEmpty() || !Hand)
	{
		return FReply::Unhandled();
	}
	FIntervalTarget Held;
	Held.Kind = bIsVault ? EIntervalTargetKind::Vault : EIntervalTargetKind::Pack;
	// A PACK CELL CARRIES ITS SLOT; A VAULT CELL CARRIES HOW MANY ARE IN IT.
	// The world's verbs ask for exactly those two things and nothing else.
	Held.X = bIsVault ? Qty : Index;
	Held.Name = Item;
	Held.Type = Item;
	Hand->UiTookTheClick = 2;
	Hand->OnOptions.Broadcast({ Held });
	return FReply::Handled();
}

void UIntervalSlotWidget::Picked()
{
	if (!Hand || Item.IsEmpty())
	{
		return;
	}
	// WHAT A THING IN THE PACK AFFORDS is the bridge's answer, derived from the
	// engine -- `wield` from EQUIPPABLE, `eat` out of healOf's own chain, and
	// `drop` for everything. The first is the default, exactly as it is for a
	// thing in the world.
	// THROUGH THE SAME DOOR AS THE RIGHT CLICK.
	//
	// This asked the bridge for the item's affordances and took the first,
	// which is the raw order the engine's tables happen to name them in -- so
	// for a weapon the first was `drop`, and a left click on the dagger a
	// citizen had walked sixty tiles and paid sixteen gold for threw it on the
	// grass. Exactly that happened, and the dagger had to be picked up again.
	//
	// The menu already knows the right order (see `OptionsFor`); the left
	// click is the menu's first line and must come from the same place, or the
	// two halves of the interaction disagree about what the obvious thing is.
	FIntervalTarget Held;
	Held.Kind = bIsVault ? EIntervalTargetKind::Vault : EIntervalTargetKind::Pack;
	Held.X = bIsVault ? Qty : Index;
	Held.Name = Item;
	Held.Type = Item;
	const TArray<FIntervalOption> Options = Hand->OptionsFor(Held);
	if (Options.Num() > 0)
	{
		Hand->ActOnWith(Options[0].Verb, Held, Options[0].Argument);
	}
}

// ---------------------------------------------------------------------------
// THE HUD.

TSharedRef<SWidget> UIntervalHudWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(
			UCanvasPanel::StaticClass());

		// ---- CHAT, ACROSS THE WHOLE BOTTOM, ALWAYS ----
		//
		// It was a 420-wide box in the corner and that was too small for what
		// it is for. The settling argument was RuneScape as it was in 2005,
		// looked up on purpose to decide this: the chat log there ran the full
		// width of the screen with the inventory as a narrow column beside it.
		// "The chat actually took a lot of space even though it didn't really
		// feel like it. Yet I guess it did because the chat became a big part
		// of the game itself."
		//
		// That is this world exactly. Its whole tempo -- a tick a second,
		// walks that take minutes, crops that take twelve -- was designed to
		// leave room for talking to strangers, and an interface that gives
		// conversation a corner is an interface arguing with the design. So
		// the band runs from the left edge to the pack column and is deep
		// enough to hold a conversation rather than the last two things said.
		//
		// It costs nothing that matters: this is a top-down view of ground,
		// and the bottom strip of it is the part furthest from the citizen,
		// who is in the middle.
		UVerticalBox* TalkColumn = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());

		Said_ = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
		Said_->SetScrollBarVisibility(ESlateVisibility::Collapsed);
		if (UVerticalBoxSlot* Slot = TalkColumn->AddChildToVerticalBox(Said_))
		{
			Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		}

		// ---- TWO CHANNELS, BECAUSE THE WORLD HAS TWO ----
		//
		// `near` reaches the people this world already says you are standing
		// with; `far` reaches the island. The engine keeps them apart on
		// purpose -- "near and far are genuinely different things to say" --
		// and a window that ran them together would be choosing for the
		// citizen which of the two they meant.
		//
		// They sit ON the entry line rather than above the log, because what
		// they change is what the NEXT thing typed will do, and a control
		// belongs beside the thing it governs.
		UHorizontalBox* SayRow = WidgetTree->ConstructWidget<UHorizontalBox>(
			UHorizontalBox::StaticClass());

		auto Channels = [&](const TCHAR* Word,
			TObjectPtr<UButton>& OutButton, TObjectPtr<UTextBlock>& OutWord)
		{
			UButton* Hit = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
			FButtonStyle Style = Hit->GetStyle();
			Style.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
			Style.Hovered.TintColor = FSlateColor(Lit);
			Style.Pressed.TintColor = FSlateColor(Lit);
			Hit->SetStyle(Style);
			UTextBlock* Say = Text(WidgetTree, Faded, 11);
			Say->SetText(FText::FromString(Word));
			if (UButtonSlot* In = Cast<UButtonSlot>(Hit->AddChild(Say)))
			{
				In->SetPadding(FMargin(7.f, 1.f, 7.f, 2.f));
			}
			SayRow->AddChildToHorizontalBox(Hit);
			OutButton = Hit;
			OutWord = Say;
		};
		Channels(TEXT("nearby"), NearTab, NearWord);
		Channels(TEXT("world"), FarTab, FarWord);
		NearTab->OnClicked.AddDynamic(this, &UIntervalHudWidget::TalkNear);
		FarTab->OnClicked.AddDynamic(this, &UIntervalHudWidget::TalkFar);

		Entry = WidgetTree->ConstructWidget<UEditableTextBox>(
			UEditableTextBox::StaticClass());
		Entry->OnTextCommitted.AddDynamic(this, &UIntervalHudWidget::Said);
		FEditableTextBoxStyle Box = Entry->GetWidgetStyle();
		Box.TextStyle.ColorAndOpacity = FSlateColor(Parch);
		Box.TextStyle.Font.Size = 12;
		// A RECESS, NOT A SHEET OF PAPER. The box came with Slate's own light
		// style, so the one bright white rectangle in the whole interface was
		// the chat line -- which is also the thing the eye lands on last.
		Box.BackgroundColor = FSlateColor(Recess);
		Box.ForegroundColor = FSlateColor(Parch);
		Box.BackgroundImageNormal.TintColor = FSlateColor(Recess);
		Box.BackgroundImageHovered.TintColor = FSlateColor(Recess);
		Box.BackgroundImageFocused.TintColor = FSlateColor(Recess);
		Box.BackgroundImageReadOnly.TintColor = FSlateColor(Recess);
		Entry->SetWidgetStyle(Box);
		if (UHorizontalBoxSlot* Wide = SayRow->AddChildToHorizontalBox(Entry))
		{
			Wide->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
			Wide->SetVerticalAlignment(VAlign_Center);
		}
		TalkColumn->AddChildToVerticalBox(SayRow);
		ShowChannel();
		UBorder* Talk = Board(WidgetTree, TalkColumn, 9.f);
		TalkPlate = Talk;

		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Talk))
		{
			// CENTRED ON THE BOTTOM EDGE, at a fixed width.
			//
			// It ran the whole width first, which is the 2005 proportion, and
			// on this screen that was too much: "maybe the chat log is .. too
			// much? Maybe we should trim the sides. Keep it centered but not
			// take up that much of the screen." The reason the old proportion
			// does not carry over is that this is a top-down view of GROUND
			// with the camera low over it, so a band across the whole bottom
			// edge covers a useful part of the world rather than a border of
			// sky.
			//
			// A single anchor at the middle of the bottom edge with an
			// alignment of half keeps it centred whatever size the window is.
			// (The stretched version anchored both corners and set `Offsets`,
			// whose four numbers are not a rectangle: with the anchor pinned
			// to one line in y, the last of them is a HEIGHT. Passing 12 for
			// it made the band twelve pixels tall.)
			Slot->SetAnchors(FAnchors(0.5f, 1.f, 0.5f, 1.f));
			Slot->SetAlignment(FVector2D(0.5f, 1.f));
			Slot->SetPosition(FVector2D(0.f, -12.f));
			Slot->SetSize(FVector2D(ChatWide, ChatDeep));
		}

		// ---- A RUNG CLIMBED ----
		//
		// Top centre and brief. A level in this world is the thing a citizen
		// spent the afternoon on, and until now it was a number changing in a
		// panel they had to open to see it change. This is the other half of
		// the answer; the sound is the first half.
		{
			RisenLine = Text(WidgetTree, Gilt, 15);
			RisenPlate = Board(WidgetTree, RisenLine, 11.f);
			RisenPlate->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(RisenPlate))
			{
				Slot->SetAnchors(FAnchors(0.5f, 0.f, 0.5f, 0.f));
				Slot->SetAlignment(FVector2D(0.5f, 0.f));
				Slot->SetPosition(FVector2D(0.f, 150.f));
				Slot->SetAutoSize(true);
			}
			// THE CUE IS LOADED ONCE AND KEPT. Asking for it at the moment it
			// is wanted is a synchronous package load on the game thread, in
			// the one frame where a player is already being shown something.
			RisenCue = LoadObject<USoundBase>(nullptr,
				TEXT("/Game/Interval/Audio/cue_learned.cue_learned"));
		}

		// ---- §5c: A TRADE ON THE TABLE ----
		//
		// Under the practice banner, top centre, for the same reason it is
		// there: it is news, it is brief, and it must not be somewhere a
		// player has to go and look. A trade offer that scrolls past in the
		// chat is an offer missed, and the other person is standing there.
		{
			UVerticalBox* Deal = WidgetTree->ConstructWidget<UVerticalBox>(
				UVerticalBox::StaticClass());
			TradeLine = Text(WidgetTree, Parch, 13);
			if (UVerticalBoxSlot* At = Deal->AddChildToVerticalBox(TradeLine))
			{
				At->SetHorizontalAlignment(HAlign_Center);
			}
			TradeMine = Text(WidgetTree, Faded, 11);
			if (UVerticalBoxSlot* At = Deal->AddChildToVerticalBox(TradeMine))
			{
				At->SetHorizontalAlignment(HAlign_Center);
			}
			UHorizontalBox* Answers = WidgetTree->ConstructWidget<UHorizontalBox>(
				UHorizontalBox::StaticClass());
			auto Answer = [&](const TCHAR* Word, const FLinearColor& Tint,
				TObjectPtr<UButton>& OutButton, TObjectPtr<UTextBlock>& OutWord)
			{
				UButton* Hit = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
				FButtonStyle Style = Hit->GetStyle();
				Style.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
				Style.Hovered.TintColor = FSlateColor(Lit);
				Style.Pressed.TintColor = FSlateColor(Lit);
				Hit->SetStyle(Style);
				UTextBlock* Say = Text(WidgetTree, Tint, 12);
				Say->SetText(FText::FromString(Word));
				if (UButtonSlot* In = Cast<UButtonSlot>(Hit->AddChild(Say)))
				{
					In->SetPadding(FMargin(11.f, 2.f, 11.f, 3.f));
				}
				Answers->AddChildToHorizontalBox(Hit);
				OutButton = Hit;
				OutWord = Say;
			};
			// THE PRICE, TYPED. Sits above the answers because it is a
			// question being asked of you, not an answer you are giving.
			PriceBox = WidgetTree->ConstructWidget<UEditableTextBox>(
				UEditableTextBox::StaticClass());
			// The hint is the trade's question; `FillTrade` replaces the line
			// above the box when another deed is doing the asking.
			PriceBox->SetHintText(FText::FromString(TEXT("a number, then enter")));
			{
				// `Sum`, not `Box`: the chat line's own style is already
				// called that in this scope.
				FEditableTextBoxStyle Sum = PriceBox->GetWidgetStyle();
				Sum.TextStyle.ColorAndOpacity = FSlateColor(Parch);
				Sum.TextStyle.Font.Size = 12;
				Sum.BackgroundColor = FSlateColor(Recess);
				Sum.ForegroundColor = FSlateColor(Parch);
				Sum.BackgroundImageNormal.TintColor = FSlateColor(Recess);
				Sum.BackgroundImageHovered.TintColor = FSlateColor(Recess);
				Sum.BackgroundImageFocused.TintColor = FSlateColor(Recess);
				Sum.BackgroundImageReadOnly.TintColor = FSlateColor(Recess);
				PriceBox->SetWidgetStyle(Sum);
			}
			PriceBox->OnTextCommitted.AddDynamic(this, &UIntervalHudWidget::Priced);
			PriceBox->SetVisibility(ESlateVisibility::Collapsed);
			if (UVerticalBoxSlot* At = Deal->AddChildToVerticalBox(PriceBox))
			{
				At->SetHorizontalAlignment(HAlign_Fill);
				At->SetPadding(FMargin(0.f, 4.f, 0.f, 2.f));
			}
			Answer(TEXT("take it"), Gilt, TakeTab, TakeWord);
			Answer(TEXT("no"), Faded, DropTab, DropWord);
			TakeTab->OnClicked.AddDynamic(this, &UIntervalHudWidget::TakeTrade);
			DropTab->OnClicked.AddDynamic(this, &UIntervalHudWidget::DropTrade);
			if (UVerticalBoxSlot* At = Deal->AddChildToVerticalBox(Answers))
			{
				At->SetHorizontalAlignment(HAlign_Center);
				At->SetPadding(FMargin(0.f, 3.f, 0.f, 0.f));
			}
			TradePlate = Board(WidgetTree, Deal, 9.f);
			TradePlate->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(TradePlate))
			{
				Slot->SetAnchors(FAnchors(0.5f, 0.f, 0.5f, 0.f));
				Slot->SetAlignment(FVector2D(0.5f, 0.f));
				Slot->SetPosition(FVector2D(0.f, 86.f));
				Slot->SetAutoSize(true);
			}
		}

		// ---- §6g: THE COUNTER, WHEN THERE IS ONE ----
		//
		// Left of centre and clear of everything else: the map is top right,
		// the pack bottom right, the chat bottom centre, and a vault drawn
		// over any of those would cover the very thing a citizen is moving
		// goods to and from.
		{
			UVerticalBox* Counter = WidgetTree->ConstructWidget<UVerticalBox>(
				UVerticalBox::StaticClass());
			VaultHead = Text(WidgetTree, Gilt, 12);
			VaultHead->SetText(FText::FromString(TEXT("vault")));
			if (UVerticalBoxSlot* At = Counter->AddChildToVerticalBox(VaultHead))
			{
				At->SetHorizontalAlignment(HAlign_Center);
				At->SetPadding(FMargin(0.f, 0.f, 0.f, 5.f));
			}
			VaultSlots = WidgetTree->ConstructWidget<UUniformGridPanel>(
				UUniformGridPanel::StaticClass());
			VaultSlots->SetSlotPadding(FMargin(2.f));
			// AS WIDE AS THE PACK AND DEEPER. A vault holds many more kinds
			// than a pack does, and a citizen reads it as a wall of things
			// rather than a list -- so the grid is the pack's width, which
			// also makes the two read as the same object in two places.
			for (int32 i = 0; i < VaultSlotsShown; ++i)
			{
				UIntervalSlotWidget* Cell = CreateWidget<UIntervalSlotWidget>(
					GetOwningPlayer(), UIntervalSlotWidget::StaticClass());
				if (!Cell)
				{
					continue;
				}
				Cell->Index = i;
				Cell->bIsVault = true;
				VaultCells.Add(Cell);
				VaultSlots->AddChildToUniformGrid(Cell, i / PackAcross, i % PackAcross);
			}
			Counter->AddChildToVerticalBox(VaultSlots);
			VaultPlate = Board(WidgetTree, Counter, 8.f);
			VaultPlate->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(VaultPlate))
			{
				Slot->SetAnchors(FAnchors(0.f, 0.5f, 0.f, 0.5f));
				Slot->SetAlignment(FVector2D(0.f, 0.5f));
				Slot->SetPosition(FVector2D(18.f, 0.f));
				Slot->SetAutoSize(true);
			}
		}

		// ---- §0: WHICH WORLD THIS IS, ACROSS THE TOP ----
		//
		// A practice of the world is the same island computed from the same
		// seed, so it is indistinguishable from the country by looking at it.
		// That is the point of it and also the one thing that must never be
		// allowed to stand: the window has to say so, permanently, in a place
		// the eye passes over anyway.
		//
		// Top centre, because that is the one part of a top-down view nothing
		// else uses -- the map is top right, the pack bottom right, the chat
		// bottom centre -- and because a banner in a corner is a banner people
		// stop seeing.
		{
			UVerticalBox* Saying = WidgetTree->ConstructWidget<UVerticalBox>(
				UVerticalBox::StaticClass());
			PracticeWord = Text(WidgetTree, Parch, 13);
			PracticeWord->SetText(FText::FromString(
				TEXT("a practice of the world. nothing here is real")));
			if (UVerticalBoxSlot* At = Saying->AddChildToVerticalBox(PracticeWord))
			{
				At->SetHorizontalAlignment(HAlign_Center);
			}
			// THE WAIT, AND THEN THE DOOR. One line that counts down and then
			// becomes the thing you press, rather than a countdown in one
			// place and a button somewhere else: a resident glances up once.
			CrossTab = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
			FButtonStyle Style = CrossTab->GetStyle();
			Style.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
			Style.Hovered.TintColor = FSlateColor(Lit);
			Style.Pressed.TintColor = FSlateColor(Lit);
			CrossTab->SetStyle(Style);
			CrossWord = Text(WidgetTree, Faded, 11);
			if (UButtonSlot* In = Cast<UButtonSlot>(CrossTab->AddChild(CrossWord)))
			{
				In->SetPadding(FMargin(9.f, 1.f, 9.f, 2.f));
			}
			CrossTab->OnClicked.AddDynamic(this, &UIntervalHudWidget::Cross);
			if (UVerticalBoxSlot* At = Saying->AddChildToVerticalBox(CrossTab))
			{
				At->SetHorizontalAlignment(HAlign_Center);
			}
			PracticePlate = Board(WidgetTree, Saying, 9.f);
			PracticePlate->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(PracticePlate))
			{
				Slot->SetAnchors(FAnchors(0.5f, 0.f, 0.5f, 0.f));
				Slot->SetAlignment(FVector2D(0.5f, 0.f));
				Slot->SetPosition(FVector2D(0.f, 12.f));
				Slot->SetAutoSize(true);
			}
		}

		// ---- THE PACK, BOTTOM RIGHT, ALWAYS ----
		//
		// SLOTS AND NOTHING ELSE. There was a "pack  11 of 12 free" line over
		// it and it is gone: the grid IS the count. A player glancing down
		// mid-swing reads the empty sockets, which is faster than reading a
		// sentence about them and is the whole reason the pack is on screen.
		Slots = WidgetTree->ConstructWidget<UUniformGridPanel>(
			UUniformGridPanel::StaticClass());
		Slots->SetSlotPadding(FMargin(2.f));
		// THREE ACROSS, FOUR DOWN, which is the other half of giving the chat
		// the bottom of the screen: a 4x3 pack is a wide block sitting where
		// the conversation wants to be, and a 3x4 one is a column at the edge.
		// Twelve slots read as easily either way.
		for (int32 i = 0; i < PackSlots; ++i)
		{
			UIntervalSlotWidget* Cell = CreateWidget<UIntervalSlotWidget>(
				GetOwningPlayer(), UIntervalSlotWidget::StaticClass());
			if (!Cell)
			{
				continue;
			}
			Cell->Index = i;
			Cells.Add(Cell);
			Slots->AddChildToUniformGrid(Cell, i / PackAcross, i % PackAcross);
		}
		UBorder* Bag = Board(WidgetTree, Slots, 6.f);

		// ---- THE THREE DOORS, AND WHAT IS BEHIND THEM ----
		//
		// Stacked above the pack in the same corner, so the whole of what a
		// citizen carries and is sits in one place under the hand that is
		// already there. The sheet opens UPWARDS out of the tabs, because the
		// pack must not move when one is opened -- a slot that shifts under
		// the cursor is a slot that gets clicked by mistake.
		// ONE COLUMN, ONE WIDTH.
		//
		// The vitals strip, the three tabs and the pack were three boards that
		// each sized themselves to their own contents, so the stack came out
		// as three different widths in a stepped heap: "align the tabs above
		// the pack with the pack, so it is coherent in size/scale... so it all
		// looks like one coherent element kinda". They share a width now, and
		// because there are three tabs and the pack is three across, each tab
		// lands exactly over the column of slots beneath it.
		UVerticalBox* Corner = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());
		Column = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Column->SetWidthOverride(PackWide);
		Column->AddChild(Corner);

		SheetBody = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());
		UVerticalBox* Leaf = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());
		SheetHead = Text(WidgetTree, Lustre, 11);
		if (UVerticalBoxSlot* Slot = Leaf->AddChildToVerticalBox(SheetHead))
		{
			Slot->SetPadding(FMargin(2.f, 0.f, 0.f, 5.f));
		}
		Leaf->AddChildToVerticalBox(SheetBody);
		Sheet = Board(WidgetTree, Leaf, 9.f);
		Sheet->SetVisibility(ESlateVisibility::Collapsed);
		// ---- BESIDE THE PACK, NOT ON TOP OF IT ----
		//
		// The sheet used to be the first thing in the right-hand column, and
		// the column is anchored to the BOTTOM of the screen and grows upward.
		// The minimap is anchored to the TOP and grows down. They are two
		// stacks that know nothing about each other, so opening the sheet
		// simply made the bottom one taller until it reached the map -- and
		// the column draws at z-order 1, so it went over it. Half the minimap
		// disappeared the moment a player looked at what they were wearing,
		// which is the moment they are most likely to also want the map.
		//
		// Its own slot, a column's width to the left, is the whole fix: the
		// sheet can now be as long as the book is without touching anything,
		// and the two columns read as the pair they are.
		SheetBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		SheetBox->SetWidthOverride(PackWide);
		SheetBox->AddChild(Sheet);
		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(SheetBox))
		{
			Slot->SetAnchors(FAnchors(1.f, 1.f, 1.f, 1.f));
			Slot->SetAlignment(FVector2D(1.f, 1.f));
			Slot->SetPosition(FVector2D(-12.f - PackWide - 8.f, -12.f));
			Slot->SetAutoSize(true);
			Slot->SetZOrder(1);
		}

		// ---- AND THE ISLAND, WHICH GETS A PANEL AND NOT A SHEET ----
		//
		// The other three doors open a sheet inside the pack's column, which
		// is three slots wide. An 896-tile island in a column that narrow is
		// not a map, it is a smudge -- so this one opens in the middle of the
		// screen at one pixel a tile, the way a map you actually consult
		// behaves, and closes again on the same click that opened it.
		WorldMap = CreateWidget<UIntervalWorldMapWidget>(
			GetOwningPlayer(), UIntervalWorldMapWidget::StaticClass());
		if (WorldMap)
		{
			WorldMap->Bridge = Bridge;
			WorldMap->Hand = Hand;
			WorldMap->SetVisibility(ESlateVisibility::Visible);
			WorldPlate = Board(WidgetTree, WorldMap, 12.f);
			WorldPlate->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(WorldPlate))
			{
				Slot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f));
				Slot->SetAlignment(FVector2D(0.5f, 0.5f));
				// ABOVE CENTRE, because the chat runs along the bottom and a
				// map that covers the conversation is a map that gets closed.
				Slot->SetPosition(FVector2D(0.f, -70.f));
				Slot->SetAutoSize(true);
			}
		}

		// ---- WHAT IS NEVER BEHIND A DOOR ----
		//
		// Health and coin, and how much of the day is left. These are the
		// three things a citizen checks WHILE doing something else, which by
		// the same argument as the pack means they cannot be behind a click.
		// Everything else about the citizen is behind the middle tab.
		// ---- TWO SHORT LINES, NOT ONE LONG ONE ----
		//
		// This strip is HAlign_Fill inside the pack's column, so it is exactly
		// as wide as three pack slots and not a pixel more. One line already
		// filled it -- "64 health  6 gold  t358646" reaches the right-hand edge --
		// so the allowance added beside it was simply CLIPPED: the data
		// arrived, the widget existed, the text was set, and nothing appeared,
		// which is the most misleading way for a layout to fail.
		//
		// So it reads down instead of across. What a citizen IS goes on top;
		// what the clock is doing goes underneath, quieter and smaller,
		// because it is the line you glance at rather than read.
		UVerticalBox* Reading = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());
		Vitals = Text(WidgetTree, Lustre, 12);
		Vitals->SetJustification(ETextJustify::Center);
		Reading->AddChildToVerticalBox(Vitals);

		UHorizontalBox* Clockline = WidgetTree->ConstructWidget<UHorizontalBox>(
			UHorizontalBox::StaticClass());
		if (UVerticalBoxSlot* At = Reading->AddChildToVerticalBox(Clockline))
		{
			At->SetHorizontalAlignment(HAlign_Center);
			At->SetPadding(FMargin(0.f, 1.f, 0.f, 0.f));
		}
		// ---- AND HOW MUCH OF THE DAY IS LEFT ----
		//
		// A citizen may be present for ninety minutes a day. When it is spent
		// they are STOOD DOWN -- still standing there, still drawn, and no
		// longer able to act -- and from inside the window that is
		// indistinguishable from a broken bridge: deeds stop landing and
		// nothing says why. The frame has carried the allowance since the day
		// the seam was written and nothing has ever drawn it.
		//
		// Its own block, because it is the only thing on this line that
		// changes colour. It sits beside the vitals rather than in a panel of
		// its own: it is one short word, and the HUD does not need another
		// box.
		Allowance = Text(WidgetTree, Faded, 11);
		if (UHorizontalBoxSlot* At = Clockline->AddChildToHorizontalBox(Allowance))
		{
			At->SetVerticalAlignment(VAlign_Center);
			At->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
		}
		// AND THE WORLD'S OWN CLOCK, which used to ride on the line above.
		Clock = Text(WidgetTree, Faded, 11);
		if (UHorizontalBoxSlot* At = Clockline->AddChildToHorizontalBox(Clock))
		{
			At->SetVerticalAlignment(VAlign_Center);
		}
		UBorder* Strip = Board(WidgetTree, Reading, 6.f);
		if (UVerticalBoxSlot* Slot = Corner->AddChildToVerticalBox(Strip))
		{
			Slot->SetPadding(FMargin(0.f, 0.f, 0.f, 5.f));
			Slot->SetHorizontalAlignment(HAlign_Fill);
		}

		// ---- WHAT HAS BEEN LEARNED, ABOVE THE PACK ----
		//
		// Three across, matching the pack beneath it and the tabs above it, so
		// the whole right-hand column is one object at one width. Each cell is
		// the craft's tool with its level on it -- small, because this is
		// something a player GLANCES at while doing something else, which is
		// the whole reason it is out here instead of behind a tab.
		{
			// WORDS, NOT SYMBOLS.
			//
			// The first cut borrowed each craft's tool sprite -- a hatchet for
			// woodcraft, a pickaxe for earthcraft -- which needed no new art
			// and was the wrong answer: "maybe just use the skill names
			// instead.. those symbols don't really explain the skills well".
			// A hatchet reads as a hatchet. Half the crafts have no tool that
			// stands for them at all, and `bones` for mourning or a chart for
			// wayfaring are riddles rather than icons.
			//
			// A name is nine short rows and every one of them is unambiguous,
			// which for a thing you are meant to GLANCE at settles it. The
			// shape is the character sheet's own: the word on the left in
			// brass, the number on the right.
			Crafts = WidgetTree->ConstructWidget<UUniformGridPanel>(
				UUniformGridPanel::StaticClass());
			Crafts->SetSlotPadding(FMargin(0.f, 0.f));
			for (int32 i = 0; i < CraftTools.Num(); ++i)
			{
				// A FILL BEHIND THE WORDS, not a bar beside them.
				//
				// Nine separate bars in a column three slots wide would be
				// nine more things to look at; the same information as a dim
				// wash behind each name reads at a glance and takes no room
				// at all. It is the progress through THIS level, which is the
				// only question a bar can answer honestly.
				UOverlay* Behind = WidgetTree->ConstructWidget<UOverlay>(
					UOverlay::StaticClass());
				UProgressBar* Through = WidgetTree->ConstructWidget<UProgressBar>(
					UProgressBar::StaticClass());
				FProgressBarStyle Look;
				Look.BackgroundImage.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
				Look.FillImage.TintColor = FSlateColor(FLinearColor(Gilt.R, Gilt.G, Gilt.B, 0.20f));
				Through->SetWidgetStyle(Look);
				Through->SetPercent(0.f);
				if (UOverlaySlot* In = Behind->AddChildToOverlay(Through))
				{
					In->SetHorizontalAlignment(HAlign_Fill);
					In->SetVerticalAlignment(VAlign_Fill);
				}
				CraftBars.Add(Through);
				UHorizontalBox* Line = WidgetTree->ConstructWidget<UHorizontalBox>(
					UHorizontalBox::StaticClass());
				UTextBlock* Word = Text(WidgetTree, Brass, 10);
				Word->SetText(FText::FromString(CraftTools[i].Key));
				if (UHorizontalBoxSlot* At = Line->AddChildToHorizontalBox(Word))
				{
					At->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
					At->SetVerticalAlignment(VAlign_Center);
				}
				UTextBlock* Rung = Text(WidgetTree, Parch, 10);
				Rung->SetText(FText::FromString(TEXT("1")));
				if (UHorizontalBoxSlot* At = Line->AddChildToHorizontalBox(Rung))
				{
					At->SetVerticalAlignment(VAlign_Center);
					At->SetPadding(FMargin(4.f, 0.f, 1.f, 0.f));
				}
				CraftLevels.Add(Rung);
				if (UOverlaySlot* In = Behind->AddChildToOverlay(Line))
				{
					In->SetHorizontalAlignment(HAlign_Fill);
					In->SetVerticalAlignment(VAlign_Center);
				}
				// AND WHAT THE LAST DEED PAID, OVER THE BAR IT MOVED.
				//
				// In the overlay rather than in the line, so that it costs the
				// name and the number no room and cannot shift them when it
				// appears. Held off the right edge far enough to clear the
				// level, which is the one thing on this row that must stay
				// readable while a number is fading over it.
				UTextBlock* Gain = Text(WidgetTree, Gilt, 10);
				Gain->SetText(FText::GetEmpty());
				Gain->SetVisibility(ESlateVisibility::Collapsed);
				if (UOverlaySlot* In = Behind->AddChildToOverlay(Gain))
				{
					In->SetHorizontalAlignment(HAlign_Right);
					In->SetVerticalAlignment(VAlign_Center);
					In->SetPadding(FMargin(0.f, 0.f, 24.f, 0.f));
				}
				CraftGains.Add(Gain);
				GainAt.Add(-1e9);
				GainSum.Add(0);
				CraftRows.Add(Behind);
				Crafts->AddChildToUniformGrid(Behind, i, 0);
			}
			UBorder* Learned = Board(WidgetTree, Crafts, 5.f);
			if (UVerticalBoxSlot* Slot = Corner->AddChildToVerticalBox(Learned))
			{
				Slot->SetPadding(FMargin(0.f, 0.f, 0.f, 5.f));
				Slot->SetHorizontalAlignment(HAlign_Fill);
			}
		}

		UHorizontalBox* TabRow = WidgetTree->ConstructWidget<UHorizontalBox>(
			UHorizontalBox::StaticClass());
		// A FOURTH DOOR, AND IT COSTS NO NEW ROOM. The row fills the pack's
		// width however many tabs are in it, so the island joins what is worn,
		// who you are and what you know without the HUD growing at all.
		const TCHAR* Icons[] = { TEXT("steel-helm"), TEXT("sigil"), TEXT("chart"), TEXT("charter") };
		const TCHAR* Titles[] = { TEXT("worn"), TEXT("the citizen"), TEXT("the book"), TEXT("the island") };
		for (int32 i = 0; i < 4; ++i)
		{
			UIntervalTabWidget* Tab = CreateWidget<UIntervalTabWidget>(
				GetOwningPlayer(), UIntervalTabWidget::StaticClass());
			if (!Tab)
			{
				continue;
			}
			Tab->Which = i;
			Tab->Icon = Icons[i];
			Tab->Title = Titles[i];
			Tab->Owner = this;
			TabButtons.Add(Tab);
			if (UHorizontalBoxSlot* Slot = TabRow->AddChildToHorizontalBox(Tab))
			{
				Slot->SetPadding(FMargin(i ? 4.f : 0.f, 0.f, 0.f, 0.f));
				Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
				Slot->SetHorizontalAlignment(HAlign_Fill);
			}
		}
		UBorder* Doors = Board(WidgetTree, TabRow, 5.f);
		if (UVerticalBoxSlot* Slot = Corner->AddChildToVerticalBox(Doors))
		{
			Slot->SetPadding(FMargin(0.f, 0.f, 0.f, 5.f));
			Slot->SetHorizontalAlignment(HAlign_Fill);
		}
		Corner->AddChildToVerticalBox(Bag);

		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Column))
		{
			Slot->SetAnchors(FAnchors(1.f, 1.f, 1.f, 1.f));
			Slot->SetAlignment(FVector2D(1.f, 1.f));
			Slot->SetPosition(FVector2D(-12.f, -12.f));
			Slot->SetAutoSize(true);
			// OVER THE MINIMAP'S COLUMN, WHICH IS ADDED AFTER IT.
			//
			// A sheet opens UPWARDS out of the tabs so the pack does not move
			// under the cursor, and with four things worn it grows far enough
			// to reach the place name under the minimap. Everything on this
			// canvas sits at zero, so the later child won and the sheet a
			// player had just opened was drawn BEHIND the word "Anchor".
			//
			// The sheet wins. It is transient, it was asked for, and the
			// minimap is still there the moment it closes.
			Slot->SetZOrder(1);
		}

		// ---- THE MINIMAP, TOP RIGHT ----
		//
		// Opposite corner to the chat and above the pack, which is where this
		// genre has always put it and, more to the point, the only corner with
		// nothing else in it. See the note on the widget for why a window onto
		// a world nine hundred tiles across cannot do without one.
		Map = CreateWidget<UIntervalMapWidget>(
			GetOwningPlayer(), UIntervalMapWidget::StaticClass());
		if (Map)
		{
			Map->Bridge = Bridge;
			Map->Hand = Hand;
			// ---- THE MAP AND ITS CAPTION SHARE A COLUMN ----
			//
			// They were two things in the canvas, each sized by its own
			// arithmetic, and arithmetic is exactly what must not decide this:
			// "it has to perfectly fit otherwise it looks even worse than
			// before", and it is right -- a caption a few units narrower than
			// the thing it captions reads as a mistake, where a caption half
			// the width would read as a choice.
			//
			// So they go in one column, the way the vitals, the tabs and the
			// pack already do, and the caption is HAlign_Fill. The width is
			// then the map's by construction: nothing computes it, nothing can
			// drift, and changing the map's size moves the caption with it.
			MapColumn = WidgetTree->ConstructWidget<UVerticalBox>(
				UVerticalBox::StaticClass());
			if (UVerticalBoxSlot* At = MapColumn->AddChildToVerticalBox(Map))
			{
				At->SetHorizontalAlignment(HAlign_Fill);
			}
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(MapColumn))
			{
				Slot->SetAnchors(FAnchors(1.f, 0.f, 1.f, 0.f));
				Slot->SetAlignment(FVector2D(1.f, 0.f));
				Slot->SetPosition(FVector2D(-12.f, 12.f));
				Slot->SetAutoSize(true);
			}
		}

		// ---- AND WHAT THIS GROUND IS CALLED ----
		//
		// A map shows a picture of the ground. It does not say where you ARE,
		// and on an island 896 by 512 with thirty-odd named places on it, a
		// picture without a name is half a map -- especially in a world whose
		// design turns on "meet me by the crooked oak" being an ordinary
		// sentence. Two citizens cannot arrange to meet anywhere if neither
		// window will say the name of the ground they are standing on.
		//
		// It gets its own small plate under the map rather than a line inside
		// it: the map is a disc in a square, and the corners of that square
		// are where the compass letters live at half-quarter angles. A name
		// written in there would collide with S or W four times per turn.
		//
		// The NAME IS THE WORLD'S. `regionNameAt` is the generator's own
		// naming, derived by the bridge, so what is written here is what is
		// written in the chat line and on everybody else's screen.
		Hereabouts = Text(WidgetTree, Gilt, 13);
		Hereabouts->SetJustification(ETextJustify::Center);
		// AS WIDE AS THE MAP IT BELONGS TO. A little plate of its own size
		// under a big square one reads as two unrelated things stacked up;
		// matched, they read as one instrument with a caption. Asked for in
		// those words -- "the place name panel should be stretched out so it
		// fits the minimap".
		WherePlate = Board(WidgetTree, Hereabouts, 6.f);
		WherePlate->SetVisibility(ESlateVisibility::Collapsed);
		if (MapColumn)
		{
			if (UVerticalBoxSlot* At = MapColumn->AddChildToVerticalBox(WherePlate))
			{
				At->SetHorizontalAlignment(HAlign_Fill);
				At->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
			}
		}

		// ---- AND WHOSE HANDS HAVE BEEN ON THE WORK HERE ----
		//
		// Under the place name, because it answers the same kind of question:
		// not what a citizen is carrying but what is going on where they are
		// standing. It appears at a furnace, an anvil or a sawpit that
		// somebody has used lately and is collapsed everywhere else, so it
		// costs nothing on an empty hillside.
		HandsLine = Text(WidgetTree, Parch, 11);
		HandsLine->SetJustification(ETextJustify::Center);
		HandsPlate = Board(WidgetTree, HandsLine, 6.f);
		HandsPlate->SetVisibility(ESlateVisibility::Collapsed);
		if (MapColumn)
		{
			if (UVerticalBoxSlot* At = MapColumn->AddChildToVerticalBox(HandsPlate))
			{
				At->SetHorizontalAlignment(HAlign_Fill);
				At->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
			}
		}

		// ---- THE POINTER, AND WHAT IT JUST DID ----
		//
		// Pixel Streaming sends the viewport and the operating system's cursor
		// is not in it, so a watcher sees a citizen set off walking with
		// nothing on screen to say why. The window draws its own.
		// A DRAWN POINTER, NOT A PLUS.
		//
		// It was a `+` in a text block, which is a crosshair and belongs to a
		// different kind of game: "I think the cursor should look a little
		// cooler... like the old MMORPGs used to have. Maybe it should even
		// change appearance if hovering a gatherable resource."
		//
		// So it is an arrow, drawn by `Tools/cursors.py` in the same tallow
		// and ink as the rest of the interface -- and it CHANGES: over a thing
		// that affords something, it becomes the tool for the job, taken from
		// the item sprites this project already renders. A pickaxe over a
		// seam, a sword over a beast. The pointer says what the click will do
		// before it is made, which on a top-down view of a hundred things is
		// worth more than any amount of decoration.
		Pointer = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		Pointer->SetVisibility(ESlateVisibility::HitTestInvisible);
		if (UTexture2D* Arrow = UIntervalSlotWidget::IconFor(TEXT("cursor-point")))
		{
			Pointer->SetBrushFromTexture(Arrow, false);
		}
		// BIGGER, AND LEANING. It was thirty-eight and nearly upright, and
		// both were reported in one line off the stream: "i think the cursor
		// should be a little bigger and more diagonal it's too
		// straight/vertical". The lean is in `Tools/cursors.py`, which now
		// swings the blade twenty-four degrees about its tip; the size is
		// here, because the drawing fills the same share of its canvas as
		// before and only the canvas got bigger.
		Pointer->SetBrushSize(FVector2D(50.f, 50.f));
		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Pointer))
		{
			Slot->SetAutoSize(true);
			// The TIP is the hot spot, and the tip is the top-left corner of
			// the drawing -- so the sprite hangs down and right of the point,
			// exactly as a cursor does. The lean is applied ABOUT the tip in
			// `cursors.py` for this reason: the blade swings out from under
			// the point and the point does not move, so this fraction is the
			// same as it was and the pointer still clicks where it looks.
			Slot->SetAlignment(FVector2D(0.047f, 0.031f));
		}

		Struck = Text(WidgetTree, Parch, 12);
		StruckPlate = Board(WidgetTree, Struck, 7.f);
		StruckPlate->SetVisibility(ESlateVisibility::Collapsed);
		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(StruckPlate))
		{
			Slot->SetAnchors(FAnchors(0.5f, 1.f, 0.5f, 1.f));
			Slot->SetAlignment(FVector2D(0.5f, 1.f));
			Slot->SetPosition(FVector2D(0.f, -14.f));
			Slot->SetAutoSize(true);
		}

		// ---- §6c: AND THE BREAK WHEN A CITIZEN GOES DOWN ----
		//
		// Added last, so it lies over the pack, the chat and the pointer. A
		// death that left the interface fully legible underneath would be the
		// thing this exists to prevent: it has to be plainly a different state
		// and not a notification about one.
		//
		// Ink rather than black. Nothing in this interface is neutral grey and
		// a pure black veil would be the first thing in it that was; this is
		// the same ink the boards are cut from, which reads as the world being
		// shut out rather than as the renderer failing.
		DeathWash = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		DeathWash->SetBrushTintColor(FSlateColor(FLinearColor(0.038f, 0.040f, 0.052f, 1.f)));
		DeathWash->SetVisibility(ESlateVisibility::Collapsed);
		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(DeathWash))
		{
			Slot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
			Slot->SetOffsets(FMargin(0.f));
		}
		{
			UVerticalBox* Said = WidgetTree->ConstructWidget<UVerticalBox>(
				UVerticalBox::StaticClass());
			// BIG, because this is the one line in the window that is allowed
			// to be. Everything else here is something a player GLANCES at
			// while doing something; this is the thing that stopped them.
			DeathWord = Text(WidgetTree, Parch, 30);
			DeathWord->SetJustification(ETextJustify::Center);
			if (UVerticalBoxSlot* At = Said->AddChildToVerticalBox(DeathWord))
			{
				At->SetHorizontalAlignment(HAlign_Center);
			}
			// And what happens next, which is the half that makes it a break
			// rather than a failure: a citizen who has just died wants to know
			// where they are about to be and how long they have to wait.
			DeathCount = Text(WidgetTree, Faded, 14);
			DeathCount->SetJustification(ETextJustify::Center);
			if (UVerticalBoxSlot* At = Said->AddChildToVerticalBox(DeathCount))
			{
				At->SetHorizontalAlignment(HAlign_Center);
				At->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));
			}
			DeathPlate = Board(WidgetTree, Said, 18.f);
			DeathPlate->SetVisibility(ESlateVisibility::Collapsed);
			if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(DeathPlate))
			{
				Slot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f));
				Slot->SetAlignment(FVector2D(0.5f, 0.5f));
				Slot->SetAutoSize(true);
			}
		}

		WidgetTree->RootWidget = Root;
	}
	return Super::RebuildWidget();
}

void UIntervalHudWidget::Pressed(const FString& What)
{
	if (!Struck || !StruckPlate)
	{
		return;
	}
	Struck->SetText(FText::FromString(What));
	StruckPlate->SetVisibility(ESlateVisibility::HitTestInvisible);
	StruckAt = FPlatformTime::Seconds();
}

void UIntervalHudWidget::Line(const FString& Who, const FString& What,
	const FLinearColor& Tint)
{
	if (!Said_)
	{
		return;
	}
	UTextBlock* Row = Text(WidgetTree, Tint, 12);
	Row->SetAutoWrapText(true);
	Row->SetText(FText::FromString(Who.IsEmpty()
		? What : FString::Printf(TEXT("%s  %s"), *Who, *What)));
	Said_->AddChild(Row);
	// THE LAST THING SAID IS THE THING BEING READ. A chat that does not follow
	// itself is a chat you have to scroll to use, which is a chat nobody uses.
	Said_->ScrollToEnd();
	// A HUNDRED LINES IS PLENTY and an unbounded box is a leak that shows up
	// after an hour as a window that will not scroll.
	while (Said_->GetChildrenCount() > 100)
	{
		Said_->RemoveChildAt(0);
	}
}

void UIntervalHudWidget::Heard(const FIntervalSaid& Talk)
{
	SpeechLine(Talk, Bridge && Talk.SpeakerId == Bridge->GetPlayerId());
}

void UIntervalHudWidget::Cried(const FIntervalCry& Cry)
{
	// NO NAME IN FRONT OF IT. `Line` writes "who  what" when it is given a
	// speaker, and the whole point of a cry is that nobody said it: the world
	// did. An empty speaker is how this says so, and the colour is how a
	// reader tells it from the line above it without reading either.
	Line(FString(), Cry.Text, FLinearColor(0.86f, 0.70f, 0.28f, 1.f));
}

void UIntervalHudWidget::SpeechLine(const FIntervalSaid& Talk, bool bMine)
{
	if (!Said_)
	{
		return;
	}
	const bool bFar = Talk.Scope == TEXT("far");

	// WHO, WHAT THEY ARE, AND WHERE THEY ARE. A name on its own is the least
	// interesting thing about a speaker in a world with callings in it, and on
	// an island where "meet me by the crooked oak" is an ordinary sentence a
	// line with no place on it is half a message. All three come from the
	// bridge, which derives them with the world's own functions.
	FString Who = Talk.Name.IsEmpty() ? Talk.SpeakerId.Left(8) : Talk.Name;
	if (!Talk.Calling.IsEmpty())
	{
		Who += TEXT(", ") + Talk.Calling;
	}
	if (!Talk.Place.IsEmpty())
	{
		Who += TEXT(" at ") + Talk.Place;
	}
	Who += TEXT(":");

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass());

	// THE CHANNEL IS A MARK, NOT A WORD. A line to the island carries a small
	// gold bell; a line to the people beside you carries nothing, because
	// that is the ordinary case and the ordinary case should be quiet.
	if (bFar)
	{
		UTextBlock* Bell = Text(WidgetTree, Gilt, 11);
		Bell->SetText(FText::FromString(TEXT("world ")));
		if (UHorizontalBoxSlot* At = Row->AddChildToHorizontalBox(Bell))
		{
			At->SetVerticalAlignment(VAlign_Center);
			At->SetPadding(FMargin(0.f, 0.f, 4.f, 0.f));
		}
	}

	UTextBlock* Head = Text(WidgetTree, bMine ? HudEmber : Gilt, 12);
	Head->SetText(FText::FromString(Who));
	if (UHorizontalBoxSlot* At = Row->AddChildToHorizontalBox(Head))
	{
		At->SetVerticalAlignment(VAlign_Top);
		At->SetPadding(FMargin(0.f, 0.f, 6.f, 0.f));
	}

	// AND THE WORDS, WHICH ARE THE ONLY PART THAT WRAPS. The speaker's part
	// is short and fixed; the said part takes whatever is left of the line
	// and folds under itself, which is how a long sentence stays readable
	// instead of pushing the name off the edge.
	UTextBlock* What = Text(WidgetTree, Parch, 12);
	What->SetAutoWrapText(true);
	What->SetText(FText::FromString(Talk.Text));
	if (UHorizontalBoxSlot* At = Row->AddChildToHorizontalBox(What))
	{
		At->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	Said_->AddChild(Row);
	Said_->ScrollToEnd();
	while (Said_->GetChildrenCount() > 100)
	{
		Said_->RemoveChildAt(0);
	}
}

void UIntervalHudWidget::TurnTheSun()
{
	bAlwaysDay = !bAlwaysDay;
	// MIDDAY, not dawn: a quarter past is a long shadow and a low sun, which
	// is beautiful and is not what somebody asking for daylight wants.
	if (UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
	{
		Wardrobe->ForceDay = bAlwaysDay ? 0.5f : -1.f;
	}
	FillSheet();
}

void UIntervalHudWidget::Cross()
{
	// ONE WORD TO THE BRIDGE, which knows that birth is two-phase, how long
	// the wait is, and that a bare spawn with no vigil behind it is refused
	// forever with nothing said. Pressing this before the wait is ripe is not
	// an error -- the bridge answers with how much is left, and that lands in
	// the feed where every other answer from the world lands.
	if (Bridge)
	{
		Bridge->EnterWorld();
	}
}

void UIntervalHudWidget::TalkNear()
{
	Channel = TEXT("near");
	ShowChannel();
}

void UIntervalHudWidget::TalkFar()
{
	Channel = TEXT("far");
	ShowChannel();
}

void UIntervalHudWidget::ShowChannel()
{
	const bool bFar = Channel == TEXT("far");
	if (NearWord) { NearWord->SetColorAndOpacity(FSlateColor(bFar ? Faded : Gilt)); }
	if (FarWord) { FarWord->SetColorAndOpacity(FSlateColor(bFar ? Gilt : Faded)); }
	if (Entry)
	{
		// THE HINT SAYS WHO IS LISTENING. A citizen about to type should not
		// have to look up at a tab to find out whether they are talking to the
		// person in front of them or to the whole island.
		Entry->SetHintText(FText::FromString(bFar
			? TEXT("say something to the island")
			: TEXT("say something to the people here")));
	}
}

void UIntervalHudWidget::Told(const FIntervalFeedLine& Word)
{
	// No speaker: this is the world, not a citizen. A refusal is ember, a
	// notice is the quieter parchment, so the two are told apart at a glance
	// without either of them shouting.
	Line(FString(), Word.Text, Word.bRefusal ? HudEmber : Faded);
}

void UIntervalHudWidget::Said(const FText& Text_, ETextCommit::Type How)
{
	if (How != ETextCommit::OnEnter || !Bridge)
	{
		return;
	}
	const FString What = Text_.ToString().TrimStartAndEnd();
	if (!What.IsEmpty())
	{
		Bridge->SendChat(What, Channel);
	}
	if (Entry)
	{
		Entry->SetText(FText::GetEmpty());
	}
}

bool UIntervalHudWidget::PointerIsOverPanels() const
{
	// IS THE CURSOR ON THE INTERFACE OR ON THE WORLD?
	//
	// The hand reads the mouse from the player's input, which knows nothing
	// about widgets -- so a click on the pack or the chat ALSO reached the
	// world, and the world answered for whatever tile happens to lie under a
	// cursor that is over a panel. That is where the `walk here 0, 0` on a
	// pack menu came from, and why clicking the chat box walked the citizen.
	//
	// Slate knows perfectly well where its panels are; it just has to be
	// asked. Each of these caches its own rectangle from the last paint.
	// IN SLATE'S OWN COORDINATES, not the viewport's.
	//
	// `GetMousePosition` answers in viewport PIXELS and a widget's cached
	// geometry is in absolute desktop space, which on this display differ by
	// the interface scale of a little over two. Comparing the one against the
	// other put the cursor at roughly half of where it was, so the test said
	// "not over a panel" for every click that was. Slate knows where its own
	// cursor is; that is the number to use.
	if (!FSlateApplication::IsInitialized())
	{
		return false;
	}
	const FVector2D Where = FSlateApplication::Get().GetCursorPos();
	// THE ISLAND IS ON THIS LIST TOO. It is the biggest panel in the window
	// and it opens over the middle of the world -- a click on it that reached
	// the ground would send the citizen walking to whatever tile happened to
	// be under a map they were reading.
	const UWidget* Panels[] = { TalkPlate, Column, Map, Sheet, WorldPlate,
		WherePlate, VaultPlate, TradePlate };
	for (const UWidget* Panel : Panels)
	{
		if (!Panel || Panel->GetVisibility() == ESlateVisibility::Collapsed
			|| Panel->GetVisibility() == ESlateVisibility::Hidden)
		{
			continue;
		}
		const FGeometry& G = Panel->GetCachedGeometry();
		if (G.GetLocalSize().X <= 0.f)
		{
			continue;
		}
		if (G.IsUnderLocation(Where))
		{
			return true;
		}
	}
	return false;
}

void UIntervalHudWidget::OpenSheet(int32 Which)
{
	// A SECOND CLICK ON THE SAME DOOR SHUTS IT. Anything else and a player who
	// opened a sheet to glance at it has to hunt for the way back to the world.
	OpenTab = (OpenTab == Which) ? -1 : Which;
	for (UIntervalTabWidget* Tab : TabButtons)
	{
		if (Tab)
		{
			Tab->Light(Tab->Which == OpenTab);
		}
	}
	// THE ISLAND IS THE ONE THAT IS NOT A SHEET, so the sheet stays shut for
	// it and the panel opens instead. Both are driven by the same OpenTab, so
	// a click on any other door closes the map without anything special being
	// said here -- which is the behaviour a player expects and the reason the
	// tabs were made mutually exclusive in the first place.
	const bool bIsland = OpenTab == 3;
	if (Sheet)
	{
		Sheet->SetVisibility(OpenTab < 0 || bIsland ? ESlateVisibility::Collapsed
		                                           : ESlateVisibility::Visible);
	}
	if (WorldPlate)
	{
		WorldPlate->SetVisibility(bIsland ? ESlateVisibility::Visible
		                                  : ESlateVisibility::Collapsed);
	}
	FillSheet();
}

void UIntervalHudWidget::Named(const FText& Typed, ETextCommit::Type How)
{
	// ON ENTER, NOT ON EVERY KEYSTROKE. A name is permanent, and a box that
	// filed as you typed would claim `f`, then `fo`, then fail on `foo`
	// because `fo` was already taken -- by you, a moment ago.
	if (How != ETextCommit::OnEnter || !Hand)
	{
		return;
	}
	const FString Want = Typed.ToString().TrimStartAndEnd().ToLower();
	if (Want.IsEmpty())
	{
		return;
	}
	Hand->ClaimName(Want);
	if (NameBox)
	{
		NameBox->SetText(FText::GetEmpty());
	}
}

void UIntervalHudWidget::Priced(const FText& Typed, ETextCommit::Type How)
{
	if (How != ETextCommit::OnEnter || !Hand || Hand->AskingSlot < 0)
	{
		return;
	}
	// A NUMBER, AND ONE THAT MEANS SOMETHING. The world will not take an offer
	// wanting nothing -- an item or a positive sum, it says, and omission is
	// not a representation -- so nought here is not a gift, it is a refusal
	// waiting to happen.
	const int32 Ask = FCString::Atoi(*Typed.ToString());
	if (Ask > 0)
	{
		if (!Hand->AskingVerb.IsEmpty())
		{
			// THE SAME BOX, A DIFFERENT QUESTION. The verb carries its own
			// field and its own target; this only knows that a number was
			// typed and where to send it.
			Hand->ActOnWith(Hand->AskingVerb, Hand->AskingOn, FString::FromInt(Ask));
		}
		else
		{
			Hand->OfferTrade(Hand->Asking, { Hand->AskingSlot }, FString(), Ask);
		}
	}
	Hand->AskingSlot = -1;
	Hand->Asking.Reset();
	Hand->AskingVerb.Reset();
	if (PriceBox)
	{
		PriceBox->SetText(FText::GetEmpty());
	}
}

void UIntervalHudWidget::TakeTrade()
{
	// TAKING ONE NAMES WHO OFFERED IT, which is the field the world asks for
	// and the reason the bridge sends the key as well as the name.
	const FIntervalFrame& Frame = Bridge ? Bridge->GetFrame() : GHudEmptyFrame;
	if (Hand && !Frame.OfferFrom.IsEmpty())
	{
		Hand->AcceptTrade(Frame.OfferFrom);
	}
}

void UIntervalHudWidget::DropTrade()
{
	// ONE WORD FOR BOTH ENDS. `cancel_trade` withdraws YOUR offer, and there
	// is no deed at all for refusing somebody else's -- an offer nobody takes
	// simply stands until it is withdrawn. So this button means "withdraw
	// mine" when there is one and "I am not answering that" when there is
	// not, and the second is honestly nothing more than shutting the plate.
	// A PENDING QUESTION IS DROPPED FIRST: nothing has been filed yet, so
	// there is nothing for the world to withdraw.
	if (Hand && (Hand->AskingSlot >= 0 || !Hand->AskingVerb.IsEmpty()))
	{
		Hand->AskingSlot = -1;
		Hand->Asking.Reset();
		Hand->AskingVerb.Reset();
		return;
	}
	if (Hand && Bridge && !Bridge->GetFrame().MineTo.IsEmpty())
	{
		Hand->CancelTrade();
	}
}

void UIntervalHudWidget::FillTrade()
{
	if (!TradePlate || !Bridge || !TradeLine || !TradeMine)
	{
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	const bool bTheirs = !Frame.OfferFrom.IsEmpty();
	const bool bMine = !Frame.MineTo.IsEmpty();
	// A QUESTION WAITING ON A FIGURE brings the plate up by itself: it has
	// been asked and the box is where the answer goes. Either kind counts --
	// what to want for a trade, or what to charge, lay or give.
	const bool bAsking = Hand
		&& (Hand->AskingSlot >= 0 || !Hand->AskingVerb.IsEmpty());
	if (PriceBox)
	{
		PriceBox->SetVisibility(bAsking ? ESlateVisibility::Visible
		                                : ESlateVisibility::Collapsed);
	}
	if (!bTheirs && !bMine && !bAsking)
	{
		TradePlate->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	TradePlate->SetVisibility(ESlateVisibility::Visible);
	if (bAsking && !bTheirs && !bMine)
	{
		TradeLine->SetText(FText::FromString(Hand->AskingVerb.IsEmpty()
			? TEXT("what do you want for it?")
			: *Hand->AskingFor));
		TradeMine->SetText(FText::GetEmpty());
		if (TakeTab)
		{
			TakeTab->SetVisibility(ESlateVisibility::Collapsed);
		}
		if (DropWord)
		{
			DropWord->SetText(FText::FromString(TEXT("never mind")));
		}
		return;
	}
	if (bTheirs)
	{
		TradeLine->SetText(FText::FromString(FString::Printf(
			TEXT("%s offers you  %s   for %s"),
			*Frame.OfferName, *Frame.OfferGives, *Frame.OfferWants)));
	}
	else
	{
		TradeLine->SetText(FText::FromString(FString::Printf(
			TEXT("you offered %s  %s   for %s"),
			*Frame.MineTo, *Frame.MineGives, *Frame.MineWants)));
	}
	// BOTH AT ONCE IS POSSIBLE and it is not a muddle: two people may each
	// have an offer out. The headline is always the one waiting on YOU.
	TradeMine->SetText(FText::FromString(bTheirs && bMine
		? FString::Printf(TEXT("(yours to %s still stands)"), *Frame.MineTo)
		: FString()));
	if (TakeTab)
	{
		TakeTab->SetVisibility(bTheirs ? ESlateVisibility::Visible
		                               : ESlateVisibility::Collapsed);
	}
	if (DropWord)
	{
		DropWord->SetText(FText::FromString(bMine ? TEXT("withdraw mine")
		                                          : TEXT("no")));
	}
}

// HOW LONG A NUMBER STAYS. Long enough to be read by somebody who is looking
// at their citizen rather than at the corner, and short enough that two deeds
// a second apart do not queue up behind each other.
static constexpr double GainShown = 1.8;

void UIntervalHudWidget::FillCrafts()
{
	if (!Bridge || CraftLevels.Num() == 0)
	{
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (Frame.Levels.Num() == 0)
	{
		return;
	}
	FString Risen;
	int32 RisenTo = 0;
	for (int32 i = 0; i < CraftTools.Num() && i < CraftLevels.Num(); ++i)
	{
		const FString& Craft = CraftTools[i].Key;
		const FIntervalCraft* At = Frame.Levels.Find(Craft);
		const int32 Now = At ? At->Level : 0;
		if (CraftLevels[i])
		{
			CraftLevels[i]->SetText(FText::FromString(FString::FromInt(Now)));
			// A CRAFT NEVER PRACTISED IS DIMMED, so the eye finds the ones
			// this citizen actually does. Level one is where everybody starts
			// and says nothing about them.
			CraftLevels[i]->SetColorAndOpacity(FSlateColor(Now > 1 ? Lustre : Faded));
		}
		// HOW FAR THROUGH THIS LEVEL, and the numbers behind it on hover.
		if (At && CraftBars.IsValidIndex(i) && CraftBars[i])
		{
			const int32 Span = At->Next - At->From;
			CraftBars[i]->SetPercent(Span > 0
				? FMath::Clamp(float(At->Xp - At->From) / float(Span), 0.f, 1.f)
				: 1.f);
		}
		// ---- WHAT THE LAST DEED PAID ----
		//
		// A subtraction, not a message: the world sends every craft's
		// experience every interval, so the window already knows. Nothing new
		// crosses the wire for this.
		if (At && GainAt.IsValidIndex(i))
		{
			const int32* Before = XpWas.Find(Craft);
			if (Before && At->Xp > *Before)
			{
				const double When = FPlatformTime::Seconds();
				// A SECOND GAIN WHILE THE FIRST IS STILL SHOWING ADDS TO IT.
				//
				// Gathering pays every interval, so a fresh number each second
				// would be a flicker in the corner of the eye rather than
				// something read. One number that grows while the work goes on
				// is both quieter and more use: it says what the last few
				// swings were worth.
				GainSum[i] = (When - GainAt[i] < GainShown)
					? GainSum[i] + (At->Xp - *Before)
					: At->Xp - *Before;
				GainAt[i] = When;
			}
			XpWas.Add(Craft, At->Xp);
		}
		if (CraftGains.IsValidIndex(i) && CraftGains[i] && GainAt.IsValidIndex(i))
		{
			const double Since = FPlatformTime::Seconds() - GainAt[i];
			if (Since < GainShown && GainSum[i] > 0)
			{
				CraftGains[i]->SetText(FText::FromString(
					FString::Printf(TEXT("+%d"), GainSum[i])));
				CraftGains[i]->SetVisibility(ESlateVisibility::HitTestInvisible);
				const float Through = float(Since / GainShown);
				// A FEW PIXELS, NOT A CLIMB. See CraftGains in the header for
				// why this does not leave its own row.
				CraftGains[i]->SetRenderTranslation(FVector2D(0.f, -7.f * Through));
				// Held at full for the first third so it can be READ, then
				// away. A number that starts fading the instant it appears is
				// a number nobody catches.
				CraftGains[i]->SetRenderOpacity(Through < 0.34f
					? 1.f
					: FMath::Clamp(1.f - (Through - 0.34f) / 0.66f, 0.f, 1.f));
			}
			else if (CraftGains[i]->GetVisibility() != ESlateVisibility::Collapsed)
			{
				CraftGains[i]->SetVisibility(ESlateVisibility::Collapsed);
			}
		}
		if (At && CraftRows.IsValidIndex(i) && CraftRows[i])
		{
			// THE WHOLE TRUTH, but only when asked for. A strip that printed
			// "280 xp, 35 to go" on every one of nine rows would be a wall of
			// arithmetic beside the pack; hovering is the gesture for "tell
			// me more about this one".
			CraftRows[i]->SetToolTipText(FText::FromString(At->Next > 0
				? FString::Printf(TEXT("%s  %d\n%d xp, %d to level %d"),
					*Craft, At->Level, At->Xp, At->Next - At->Xp, At->Level + 1)
				: FString::Printf(TEXT("%s  %d\n%d xp, the top of the ladder"),
					*Craft, At->Level, At->Xp)));
		}
		// A RUNG CLIMBED. Not on the first frame of a session: everything has
		// "just arrived" at whatever it is, and announcing nine of them at the
		// gate would teach a player to ignore the banner by the time anything
		// real happened.
		const int32* Was = Rungs.Find(Craft);
		if (Was && Now > *Was && Risen.IsEmpty())
		{
			Risen = Craft;
			RisenTo = Now;
		}
		Rungs.Add(Craft, Now);
	}
	if (!Risen.IsEmpty() && RisenPlate && RisenLine)
	{
		// SAID PLAINLY. "woodcraft 6" is a table entry and "a rung climbed" --
		// which is what this called it in the log -- is a phrase nobody uses:
		// "let's just make it 'level up: your woodcraft level is now 6'".
		// The banner is the one place in this window that exists purely to be
		// read in a hurry, so it says the whole sentence.
		RisenLine->SetText(FText::FromString(FString::Printf(
			TEXT("level up: your %s level is now %d"), *Risen, RisenTo)));
		RisenPlate->SetVisibility(ESlateVisibility::Visible);
		RisenAt = FPlatformTime::Seconds();
		UE_LOG(LogTemp, Log, TEXT("[interval] level up: %s is now %d"),
			*Risen, RisenTo);
		if (RisenCue)
		{
			// AT THE EAR, not in the world: this is something the citizen
			// knows about themselves, not a noise a place makes.
			UGameplayStatics::PlaySound2D(this, RisenCue);
		}
	}
	// EIGHT SECONDS, then gone. Four was the first guess and it is too quick
	// for something meant to read as an EVENT -- a citizen mid-swing has not
	// looked up yet when it has already gone, and the whole point was that a
	// rung should not pass unnoticed. It is still not a box to dismiss: this
	// world does not stop for anything, and a banner that waited for a click
	// would be the first thing that did.
	if (RisenPlate && RisenPlate->GetVisibility() == ESlateVisibility::Visible
		&& FPlatformTime::Seconds() - RisenAt > 8.0)
	{
		RisenPlate->SetVisibility(ESlateVisibility::Collapsed);
	}
}

// HOW LONG AGO, IN WORDS. The world counts intervals and a citizen thinks in
// minutes, so the conversion happens here, using the world's own interval
// length rather than assuming it is a second.
static FString Ago(int32 Intervals, double Seconds)
{
	const int32 Mins = FMath::FloorToInt((Intervals * FMath::Max(Seconds, 0.001)) / 60.0);
	if (Mins <= 0)
	{
		return TEXT("just now");
	}
	if (Mins < 60)
	{
		return FString::Printf(TEXT("%dm ago"), Mins);
	}
	return FString::Printf(TEXT("%dh %dm ago"), Mins / 60, Mins % 60);
}

// HOW LONG THE BREAK TAKES TO ARRIVE AND TO LIFT. Half a second in, which is
// slow enough to read as the world closing over somebody and fast enough that
// it is fully there well inside the five intervals a death lasts. Out is
// quicker: the citizen is already standing somewhere else and wants to see it.
static constexpr float GriefIn = 0.5f, GriefOut = 0.28f;

void UIntervalHudWidget::FillDeath(float DeltaSeconds)
{
	if (!DeathWash || !DeathPlate || !Bridge)
	{
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	// THE WORLD'S OWN ACCOUNT OF IT, which is hit points and a tick. There is
	// no "dead" flag to read: §6c says a citizen is down when they have no
	// health left, and `deadUntil` says when the world will give them back.
	int32 Hp = 1;
	if (Frame.bHasMe)
	{
		if (const FString* Told = Frame.Me.Fields.Find(TEXT("health")))
		{
			Hp = FCString::Atoi(**Told);
		}
	}
	const bool bDown = Frame.bHasMe && Hp <= 0;
	Grief = FMath::Clamp(Grief + DeltaSeconds / (bDown ? GriefIn : -GriefOut), 0.f, 1.f);
	if (Grief <= 0.001f)
	{
		if (DeathWash->GetVisibility() != ESlateVisibility::Collapsed)
		{
			DeathWash->SetVisibility(ESlateVisibility::Collapsed);
			DeathPlate->SetVisibility(ESlateVisibility::Collapsed);
		}
		return;
	}
	DeathWash->SetVisibility(ESlateVisibility::HitTestInvisible);
	DeathPlate->SetVisibility(ESlateVisibility::HitTestInvisible);
	// NOT OPAQUE. The world stays faintly visible underneath, because a
	// citizen's body is lying in it and somebody may be standing over them.
	DeathWash->SetRenderOpacity(Grief * 0.82f);
	DeathPlate->SetRenderOpacity(Grief);

	if (DeathWord)
	{
		DeathWord->SetText(FText::FromString(TEXT("You are dead")));
	}
	if (DeathCount && bDown)
	{
		// THE COUNT, OUT OF THE WORLD'S OWN CLOCK rather than a timer started
		// here: a window that counted for itself would drift from the tick
		// that actually brings the body back, and would be wrong on a frame
		// that arrived late.
		int64 Until = 0;
		if (const FString* Told = Frame.Me.Fields.Find(TEXT("deadUntil")))
		{
			Until = FCString::Atoi64(**Told);
		}
		const int64 Left = Until > 0 ? FMath::Max<int64>(0, Until - Frame.Tick) : 0;
		// Named where the founding says the dead come back, and unnamed where
		// it does not: never a word this window made up. See `ReturnPlace`.
		const FString Where = Bridge->ReturnPlace.IsEmpty()
			? FString(TEXT("where you began"))
			: IntervalName::Spoken(Bridge->ReturnPlace);
		DeathCount->SetText(FText::FromString(Left > 0
			? FString::Printf(TEXT("returning to %s in %lld"), *Where, Left)
			: FString::Printf(TEXT("returning to %s"), *Where)));
	}
}

void UIntervalHudWidget::FillHands()
{
	if (!HandsPlate || !HandsLine || !Bridge)
	{
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		HandsPlate->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	// THE WORK UNDERFOOT OR BESIDE IT, which is the world's own `atOrBeside`
	// and the same reach every deed done at a node uses.
	const FIntervalEntity* Work = nullptr;
	for (const TPair<FString, FIntervalEntity>& N : Frame.Nodes)
	{
		if (FMath::Abs(Frame.Me.X - N.Value.X)
			+ FMath::Abs(Frame.Me.Y - N.Value.Y) > 1)
		{
			continue;
		}
		if (N.Value.Fields.Contains(TEXT("hands.0.who")))
		{
			Work = &N.Value;
			break;
		}
	}
	if (!Work)
	{
		HandsPlate->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	// WHAT IT IS CALLED, in the world's words and with spaces rather than the
	// internal id: a `charcoal-clamp` is a charcoal clamp.
	const FString* Named = Work->Fields.Find(TEXT("name"));
	FString Said = (Named && !Named->IsEmpty())
		? *Named : IntervalName::Spoken(Work->Kind);
	// §7cy keeps five, and the loop stops at the first gap rather than being
	// told the number: a founding that remembers more is drawn without this
	// file knowing it changed.
	int32 Shown = 0;
	for (int32 i = 0; i < 16; ++i)
	{
		const FString* Who = Work->Fields.Find(FString::Printf(TEXT("hands.%d.who"), i));
		if (!Who || Who->IsEmpty())
		{
			break;
		}
		const FString* When = Work->Fields.Find(FString::Printf(TEXT("hands.%d.ago"), i));
		const int32 Since = When ? FCString::Atoi(**When) : 0;
		Said += FString::Printf(TEXT("\n%s  %s"), **Who,
			*Ago(Since, Bridge->GetTickSeconds()));
		++Shown;
	}
	if (Shown == 0)
	{
		HandsPlate->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	HandsLine->SetText(FText::FromString(Said));
	HandsPlate->SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UIntervalHudWidget::FillVault()
{
	if (!VaultPlate || !Bridge)
	{
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	// NOT AT A COUNTER IS NOT THE SAME AS AN EMPTY COUNTER. The bridge says
	// which, and a citizen standing at their own empty vault must see an empty
	// vault rather than be told there is no bank here.
	if (!Frame.bAtVault)
	{
		VaultPlate->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	VaultPlate->SetVisibility(ESlateVisibility::Visible);

	// IN THE WORLD'S OWN ORDER, which is whatever order the vault map came in,
	// SORTED so a cell does not move under the cursor between two frames. A
	// stack that shuffles every second is a stack nobody can click.
	TArray<FString> Kinds;
	Frame.Vault.GetKeys(Kinds);
	Kinds.Sort();
	if (VaultHead)
	{
		VaultHead->SetText(FText::FromString(Kinds.Num() == 0
			? TEXT("vault:  empty")
			: FString::Printf(TEXT("vault:  %d %s"), Kinds.Num(),
				Kinds.Num() == 1 ? TEXT("kind") : TEXT("kinds"))));
	}
	for (int32 i = 0; i < VaultCells.Num(); ++i)
	{
		UIntervalSlotWidget* Cell = VaultCells[i];
		if (!Cell)
		{
			continue;
		}
		// THE HAND AND THE BRIDGE, EVERY FRAME, exactly as the pack's own
		// cells get them. A cell without a hand draws perfectly and does
		// nothing when it is clicked, which is the most confusing state a
		// button can be in: the vault appeared, filled, highlighted under
		// the cursor, and opened no menu.
		Cell->Hand = Hand;
		Cell->Bridge = Bridge;
		if (i < Kinds.Num())
		{
			Cell->Show(Kinds[i], Frame.Vault[Kinds[i]]);
		}
		else
		{
			Cell->Show(FString(), 0);
		}
	}
}

void UIntervalHudWidget::FillSheet()
{
	if (!SheetBody || OpenTab < 0 || OpenTab == 3 || !Bridge)
	{
		return;
	}
	SheetBody->ClearChildren();
	const FIntervalFrame& Frame = Bridge->GetFrame();

	// A SMALL HELPER, because all three sheets are the same shape: a label on
	// the left in brass and the world's own answer on the right in tallow.
	auto Pair = [&](const FString& Label, const FString& Value, bool bDim)
	{
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
			UHorizontalBox::StaticClass());
		UTextBlock* Left = Text(WidgetTree, Brass, 11);
		Left->SetText(FText::FromString(Label));
		if (USizeBox* Width = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass()))
		{
			// WIDE ENOUGH FOR THE LONGEST WORD IN IT. At sixty-six,
			// `marksmanship` ran straight over its own number and
			// `hearthcraft` clipped its last letter -- the sheet read as
			// broken text rather than as a list.
			Width->SetWidthOverride(104.f);
			Width->AddChild(Left);
			Row->AddChildToHorizontalBox(Width);
		}
		UTextBlock* Right = Text(WidgetTree, bDim ? Faded : Parch, 11);
		Right->SetText(FText::FromString(Value));
		Row->AddChildToHorizontalBox(Right);
		if (UVerticalBoxSlot* Slot = SheetBody->AddChildToVerticalBox(Row))
		{
			Slot->SetPadding(FMargin(0.f, 1.f, 0.f, 1.f));
		}
	};

	auto Field = [&](const TCHAR* Key) -> FString
	{
		const FString* Found = Frame.Me.Fields.Find(Key);
		return Found ? *Found : FString();
	};

	if (OpenTab == 0)
	{
		SheetHead->SetText(FText::FromString(TEXT("WORN")));
		// The worn map is JSON on the frame, same as the pack is.
		TSharedPtr<FJsonObject> Gear;
		const FString Raw = Field(TEXT("equipment"));
		if (!Raw.IsEmpty())
		{
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
			FJsonSerializer::Deserialize(Reader, Gear);
		}
		for (const FString& Where : WornOrder)
		{
			FString Held;
			if (Gear.IsValid())
			{
				if (!Gear->TryGetStringField(Where, Held))
				{
					const TSharedPtr<FJsonObject>* Stack = nullptr;
					if (Gear->TryGetObjectField(Where, Stack) && Stack)
					{
						(*Stack)->TryGetStringField(TEXT("item"), Held);
					}
				}
			}
			// A ROW YOU CAN PRESS, which is the only way `unwield` has ever
			// been reachable by a mouse. See UIntervalWornRow.
			UIntervalWornRow* Worn = WidgetTree->ConstructWidget<UIntervalWornRow>(
				UIntervalWornRow::StaticClass());
			Worn->Gear = Where;
			Worn->Item = Held;
			Worn->Hand = Hand;
			if (UVerticalBoxSlot* Slot = SheetBody->AddChildToVerticalBox(Worn))
			{
				Slot->SetPadding(FMargin(0.f, 1.f, 0.f, 1.f));
			}
		}
	}
	else if (OpenTab == 1)
	{
		SheetHead->SetText(FText::FromString(TEXT("THE CITIZEN")));
		const FString Called = Field(TEXT("name"));
		Pair(TEXT("name"), Called.IsEmpty() ? TEXT("unnamed") : Called, Called.IsEmpty());
		// §5a: AND A LINE TO TAKE ONE ON, while there is no name to lose.
		//
		// `claim_name` has been filable since the hand was written and there
		// has never been anywhere to type into, so every citizen this window
		// has ever made has gone through their whole day as eight characters
		// of their own public key. The world asks for standing before it will
		// take one; it says so itself when the line is sent, which is the
		// right place for that sentence to come from.
		// AND ONLY WHERE IT CAN WORK. A name costs standing, and a box offered
		// to a citizen who has not earned it is a box that fails with no
		// warning. Told the price instead, a player has something to aim at.
		const FString* Earned = Frame.Me.Fields.Find(TEXT("standing"));
		const int32 Standing = Earned ? FCString::Atoi(**Earned) : 0;
		if (Called.IsEmpty() && Standing < Bridge->NameStanding)
		{
			Pair(TEXT("a name costs"), FString::Printf(TEXT("%d standing (you have %d)"),
				Bridge->NameStanding, Standing), true);
		}
		else if (Called.IsEmpty())
		{
			NameBox = WidgetTree->ConstructWidget<UEditableTextBox>(
				UEditableTextBox::StaticClass());
			NameBox->SetHintText(FText::FromString(TEXT("take a name")));
			FEditableTextBoxStyle Box = NameBox->GetWidgetStyle();
			Box.TextStyle.ColorAndOpacity = FSlateColor(Parch);
			Box.TextStyle.Font.Size = 11;
			// THE SAME RECESS THE CHAT LINE SITS IN. One interface.
			Box.BackgroundColor = FSlateColor(Recess);
			Box.ForegroundColor = FSlateColor(Parch);
			Box.BackgroundImageNormal.TintColor = FSlateColor(Recess);
			Box.BackgroundImageHovered.TintColor = FSlateColor(Recess);
			Box.BackgroundImageFocused.TintColor = FSlateColor(Recess);
			Box.BackgroundImageReadOnly.TintColor = FSlateColor(Recess);
			NameBox->SetWidgetStyle(Box);
			NameBox->OnTextCommitted.AddDynamic(this, &UIntervalHudWidget::Named);
			if (UVerticalBoxSlot* Slot = SheetBody->AddChildToVerticalBox(NameBox))
			{
				Slot->SetPadding(FMargin(0.f, 3.f, 0.f, 5.f));
			}
		}
		Pair(TEXT("standing"), FString::Printf(TEXT("%d, %d"), Frame.Me.X, Frame.Me.Y), false);
		Pair(TEXT("health"), Field(TEXT("health")), false);
		Pair(TEXT("gold"), Field(TEXT("gold")), false);
		Pair(TEXT("calling"), Field(TEXT("calling")), false);
		Pair(TEXT("doing"), Field(TEXT("action")), Field(TEXT("action")).IsEmpty());

		// THE LADDER, NOT THE BOOKKEEPING.
		//
		// This printed the raw experience the world stores, so forty felled
		// trees read as "woodcraft 240" while the strip above the pack said
		// "woodcraft 6". Two numbers for one thing, and the one on the sheet
		// was the one nobody means. It says the level, with the experience
		// after it in smaller words, because on a sheet you have opened
		// deliberately the detail is what you came for.
		int32 Shown = 0;
		for (const TPair<FString, FString>& Known : CraftTools)
		{
			const FIntervalCraft* At = Frame.Levels.Find(Known.Key);
			if (!At)
			{
				continue;
			}
			Pair(Known.Key, At->Next > 0
				? FString::Printf(TEXT("%d   (%d/%d)"), At->Level, At->Xp, At->Next)
				: FString::Printf(TEXT("%d   (%d)"), At->Level, At->Xp),
				At->Level <= 1);
			++Shown;
		}
		if (Shown == 0)
		{
			Pair(TEXT("learned"), TEXT("no craft practised yet"), true);
		}
		// ---- AND WHAT THIS CITIZEN MAY DO ABOUT THEMSELVES ----
		//
		// Swearing to a calling, swearing a stint, sounding a horn, stopping
		// following somebody, kindling a watchfire, raising a stall: none of
		// them names a target, so none could be a row on anything in the
		// world, and every one was written into the hand and left unreachable.
		//
		// They were put on the citizen's own right-click menu first, which was
		// the right instinct and the wrong place: this window does not let you
		// point at yourself, so that menu could never be opened. The sheet
		// headed THE CITIZEN is where a player already goes to read about
		// themselves, and it is where the things they do to themselves belong.
		if (Hand && Bridge)
		{
			FIntervalTarget Self;
			Self.Kind = EIntervalTargetKind::Citizen;
			Self.Id = Frame.Me.Id;
			Self.Name = Called.IsEmpty() ? Frame.Me.Id.Left(8) : Called;
			Self.X = Frame.Me.X;
			Self.Y = Frame.Me.Y;
			for (const FIntervalOption& Deed : Hand->OptionsFor(Self))
			{
				if (Deed.Verb == TEXT("walk"))
				{
					continue;   // there is nowhere to walk to on your own sheet
				}
				if (UIntervalSpellRow* Row = CreateWidget<UIntervalSpellRow>(
					GetOwningPlayer(), UIntervalSpellRow::StaticClass()))
				{
					Row->Verb = Deed.Verb;
					Row->Label = Deed.Label;
					Row->bKnown = true;
					Row->Hand = Hand;
					Row->On = Self;
					Row->bKnown = true;
					SheetBody->AddChildToVerticalBox(Row);
				}
			}
		}

		// AND THE ONE THING ON THIS SHEET THAT IS ABOUT THE WINDOW RATHER
		// THAN THE CITIZEN. It sits here because there is nowhere else a
		// player would look for it, and because it is the only choice this
		// window offers that the world has no opinion about.
		if (UIntervalSpellRow* Sun = CreateWidget<UIntervalSpellRow>(
			GetOwningPlayer(), UIntervalSpellRow::StaticClass()))
		{
			Sun->Verb = TEXT("daylight");
			// SHORT, because the sheet is the pack's width and the long form
			// ("the world's own hours") ran off the edge of it.
			Sun->Label = bAlwaysDay ? TEXT("sun: always up")
			                        : TEXT("sun: the world's hours");
			Sun->bKnown = true;
			Sun->Hud = this;
			Sun->Hand = Hand;
			SheetBody->AddChildToVerticalBox(Sun);
		}
	}
	else
	{
		const FString Book = Field(TEXT("book"));
		SheetHead->SetText(FText::FromString(
			FString::Printf(TEXT("THE %s BOOK"), *Book.ToUpper())));
		// WHICH BOOK THE CITIZEN CARRIES decides which words are in reach.
		// Both are listed and only the carried one is lit, because knowing
		// what the OTHER book holds is part of knowing this world.
		const bool bBarrow = Book.Equals(TEXT("barrow"), ESearchCase::IgnoreCase);
		// THE WORLD'S OWN LIST, not this window's copy of it. The hand-written
		// pair below is kept only for a window that has not been told yet.
		const FIntervalAffords* Told = Bridge->Books.Find(bBarrow ? TEXT("barrow") : TEXT("common"));
		const TArray<FString>& Words = Told ? Told->Verbs
			: (bBarrow ? BarrowBook : CommonBook);
		for (const FString& Word : Words)
		{
			UIntervalSpellRow* Row = CreateWidget<UIntervalSpellRow>(
				GetOwningPlayer(), UIntervalSpellRow::StaticClass());
			if (!Row)
			{
				continue;
			}
			Row->Spell = Word;
			Row->bKnown = true;
			Row->Hand = Hand;
			SheetBody->AddChildToVerticalBox(Row);
		}
		// AND THE ONE ACT IN THE BOOK THAT IS NOT A WORD.
		//
		// Three magic-stones pressed into a sigil, which is where every spell
		// in the list above gets the thing it spends. It takes no target and
		// no words, so it had nowhere to be clicked and has been filable and
		// unreachable since the book existed.
		if (UIntervalSpellRow* Press = CreateWidget<UIntervalSpellRow>(
			GetOwningPlayer(), UIntervalSpellRow::StaticClass()))
		{
			Press->Verb = TEXT("invoke");
			// SHORT, BECAUSE THE SHEET IS THE PACK'S WIDTH. "press three
			// magic-stones into a sigil" is the truthful sentence and it ran
			// off the edge of the panel; three words that say the same thing
			// fit beside the spells they belong with.
			Press->Label = TEXT("press a sigil");
			Press->bKnown = true;
			Press->Hand = Hand;
			SheetBody->AddChildToVerticalBox(Press);
		}
	}
}

void UIntervalHudWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
	Super::NativeTick(Geometry, Delta);

	// ---- THE POINTER, EVERY FRAME ----
	//
	// Not once an interval like the pack: a cursor that moves once a second is
	// worse than no cursor, because it looks like the window is broken.
	if (bShowPointer && Pointer)
	{
		if (APlayerController* PC = GetOwningPlayer())
		{
			float MX = 0.f, MY = 0.f;
			if (PC->GetMousePosition(MX, MY))
			{
				const float Scale = FMath::Max(
					UWidgetLayoutLibrary::GetViewportScale(this), 0.01f);
				if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Pointer->Slot))
				{
					Slot->SetPosition(FVector2D(MX / Scale, MY / Scale));
				}
				Pointer->SetVisibility(ESlateVisibility::HitTestInvisible);

				// WHAT IT WOULD DO, asked of the hand -- but not every frame.
				// Answering means looking at everything on a tile, and the
				// answer cannot change faster than the pointer crosses a tile.
				Hovered += Delta;
				if (Hand && Hovered > 0.12f)
				{
					Hovered = 0.f;
					const FString Verb = Hand->VerbUnderCursor();
					if (Verb != Hovering)
					{
						Hovering = Verb;
						// The tool for the job, out of the pack's own art.
						static const TMap<FString, FString> Tools = {
							// `gather` alone is chopping, mining AND fishing;
							// the kind rides after a bar. See VerbUnderCursor.
							{TEXT("gather"),   TEXT("iron-pickaxe")},
							{TEXT("gather|tree"), TEXT("iron-hatchet")},
							{TEXT("gather|oak-tree"), TEXT("iron-hatchet")},
							{TEXT("gather|ironbark-tree"), TEXT("iron-hatchet")},
							{TEXT("gather|heartwood-tree"), TEXT("iron-hatchet")},
							{TEXT("gather|fishing-spot"), TEXT("rod")},
							{TEXT("gather|eel-spot"), TEXT("rod")},
							{TEXT("gather|deep-fish-spot"), TEXT("rod")},
							{TEXT("harvest"),  TEXT("spade")},
							{TEXT("attack"),   TEXT("iron-sword")},
							{TEXT("attackp"),  TEXT("iron-sword")},
							{TEXT("buy"),      TEXT("sigil")},
							{TEXT("drink"),    TEXT("broth")},
							{TEXT("cook"),     TEXT("bread")},
							{TEXT("smith"),    TEXT("iron-mell")},
							{TEXT("smelt"),    TEXT("iron-ore")},
							{TEXT("fletch"),   TEXT("arrows")},
						};
						// THE FULL WORD FIRST, THEN THE VERB ALONE. `gather`
						// arrives as `gather|tree` where the kind matters, so
						// a kind nobody has named still gets the general
						// answer rather than no answer at all.
						const FString* Art = Tools.Find(Verb);
						if (!Art)
						{
							FString Bare, Kind;
							if (Verb.Split(TEXT("|"), &Bare, &Kind))
							{
								Art = Tools.Find(Bare);
							}
						}
						UTexture2D* Sprite = UIntervalSlotWidget::IconFor(
							Art ? *Art : TEXT("cursor-point"));
						if (Sprite)
						{
							Pointer->SetBrushFromTexture(Sprite, false);
							Pointer->SetBrushSize(FVector2D(Art ? 44.f : 38.f,
								Art ? 44.f : 38.f));
						}
					}
				}
			}
			else
			{
				Pointer->SetVisibility(ESlateVisibility::Collapsed);
			}

			// AND WHAT WAS PRESSED. The click is the cause; without it the
			// stream shows only effects.
			const bool bLeft = PC->IsInputKeyDown(EKeys::LeftMouseButton);
			const bool bRight = PC->IsInputKeyDown(EKeys::RightMouseButton);
			if (bLeft && !bWasLeft) { Pressed(TEXT("left click")); }
			if (bRight && !bWasRight) { Pressed(TEXT("right click")); }
			bWasLeft = bLeft;
			bWasRight = bRight;
		}
	}
	// ---- NOTHING UNTIL THE WORLD IS ENTERED ----
	//
	// The title card is the whole screen until somebody crosses it, and a pack
	// and a minimap sitting over it are the window talking before it has been
	// spoken to. The POINTER stays: the card has a button on it, and Pixel
	// Streaming sends the viewport without the operating system's cursor, so
	// taking the pointer away would leave a button nobody can aim at.
	{
		TActorIterator<AIntervalGate> Door(GetWorld());
		const bool bBehindTheGate = Door && Door->IsWaiting();
		const ESlateVisibility Want = bBehindTheGate
			? ESlateVisibility::Collapsed : ESlateVisibility::Visible;
		if (TalkPlate && TalkPlate->GetVisibility() != Want)
		{
			TalkPlate->SetVisibility(Want);
		}
		if (Column && Column->GetVisibility() != Want)
		{
			Column->SetVisibility(Want);
		}
		if (Map && Map->GetVisibility() != Want)
		{
			Map->SetVisibility(Want);
		}
		// The sheet has its own slot now and so needs its own line here, or a
		// citizen still behind the gate would be shown what they are wearing.
		if (SheetBox && SheetBox->GetVisibility() != Want)
		{
			SheetBox->SetVisibility(Want);
		}
	}

	if (StruckPlate && StruckPlate->GetVisibility() != ESlateVisibility::Collapsed
		&& FPlatformTime::Seconds() - StruckAt > 1.4)
	{
		StruckPlate->SetVisibility(ESlateVisibility::Collapsed);
	}

	if (!Bridge)
	{
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (Frame.Tick == LastDrawn)
	{
		return;
	}
	LastDrawn = Frame.Tick;

	// THE PACK, ONCE AN INTERVAL. The world only changes that often, and a
	// panel that rebuilds every frame is a panel that cannot be clicked.
	const FString* Raw = Frame.Me.Fields.Find(TEXT("inventory"));
	TArray<TSharedPtr<FJsonValue>> Entries;
	if (Raw)
	{
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Raw);
		FJsonSerializer::Deserialize(Reader, Entries);
	}
	int32 Used = 0;
	for (int32 i = 0; i < Cells.Num(); ++i)
	{
		FString Item;
		int32 Qty = 0;
		if (Entries.IsValidIndex(i) && Entries[i].IsValid()
			&& Entries[i]->Type == EJson::Object)
		{
			const TSharedPtr<FJsonObject>& Slot = Entries[i]->AsObject();
			Slot->TryGetStringField(TEXT("item"), Item);
			double N = 1.0;
			Slot->TryGetNumberField(TEXT("qty"), N);
			Qty = static_cast<int32>(N);
		}
		if (!Item.IsEmpty())
		{
			++Used;
		}
		Cells[i]->Hand = Hand;
		Cells[i]->Bridge = Bridge;
		Cells[i]->Show(Item, Qty);
	}
	(void)Used;   // the grid is the count; see the note where the line was

	if (Vitals)
	{
		// AS A WHOLE NUMBER. The frame carries these as JSON numbers and they
		// arrive as text the way a double prints: "64.000000 health  22.000000
		// gold", which is a debug print and not a thing a citizen reads.
		auto Whole = [&](const TCHAR* Key) -> FString
		{
			const FString* Found = Frame.Me.Fields.Find(Key);
			if (!Found)
			{
				return TEXT("--");
			}
			return FString::Printf(TEXT("%d"), FMath::RoundToInt(FCString::Atof(**Found)));
		};
		// AND THE WORLD'S OWN CLOCK.
		//
		// This world ticks once a second and every deed is stamped with the
		// tick it happened on, so the number is part of what a citizen is
		// looking at -- and it is the one thing that says at a glance whether
		// the window is keeping up. A window several hundred ticks behind
		// looks exactly like a world that has stopped accepting deeds, and
		// without the number on screen there is no way to tell those apart.
		// AND THE WORD IS "health", NOT "health".
		//
		// `health` is an abbreviation of `hitpoints`, which is a term this world
		// borrowed from other games and never needed: the engine stores the
		// field as `health` because it is a field, and a field name is not a word
		// to put in front of a player. The window said `health`, the handbook said
		// `hitpoints` and the engine's own prose said `flesh`, which is three
		// vocabularies for one number.
		//
		// The gap is two spaces rather than four because this strip is exactly
		// three pack slots wide -- 156 px, three times SlotSide -- and the note
		// where it is built records what happens when that overruns: the text
		// is silently clipped and nothing appears at all, which is the most
		// misleading way for a layout to fail.
		//
		// THE MARGIN, since the word got four characters longer. Health is two
		// digits and cannot be three, so the length is set by the fortune:
		// "64 health  12 gold" is 18 characters and "64 health  999999 gold"
		// is 22, which is exactly the length the note above measured as
		// reaching the right-hand edge. So a citizen with a six-figure hoard
		// is at the limit and one with seven would lose the end of it. If that
		// ever happens the answer is another line, not a smaller gap: this
		// strip already reads downward for exactly this reason.
		Vitals->SetText(FText::FromString(FString::Printf(
			TEXT("%s health  %s gold"), *Whole(TEXT("health")), *Whole(TEXT("gold")))));
	}
	if (Clock)
	{
		Clock->SetText(FText::FromString(FString::Printf(TEXT("t%lld"), Frame.Tick)));
	}

	if (Allowance)
	{
		// IN MINUTES, because the world ticks once a second and nobody thinks
		// in thousands of seconds. The WARNING BAND IS THE WORLD'S -- the
		// bridge sends `warn` and this only compares against it, so a founding
		// that moves the threshold moves it here with no code changed.
		if (Frame.CeilingAllow <= 0)
		{
			Allowance->SetText(FText::GetEmpty());
		}
		else if (Frame.bStoodDown)
		{
			Allowance->SetText(FText::FromString(TEXT("stood down")));
			Allowance->SetColorAndOpacity(FSlateColor(HudEmber));
		}
		else
		{
			const int32 Minutes = FMath::CeilToInt(Frame.CeilingLeft / 60.f);
			Allowance->SetText(FText::FromString(
				FString::Printf(TEXT("%d min"), Minutes)));
			Allowance->SetColorAndOpacity(FSlateColor(
				Frame.CeilingLeft <= Frame.CeilingWarn ? HudEmber : Faded));
		}
	}

	// §0: THE PRACTICE BANNER, AND THE CROSSING.
	//
	// The bridge decides which world a frame is of; this only draws it. The
	// knock goes out ONCE, without being asked for: the five minutes is a real
	// five minutes and there is no reason to make somebody find a button
	// before it starts running. The CROSSING is not automatic, because a
	// resident in the middle of something should choose when to leave.
	if (PracticePlate && CrossWord)
	{
		if (!Frame.bNought)
		{
			PracticePlate->SetVisibility(ESlateVisibility::Collapsed);
		}
		else
		{
			PracticePlate->SetVisibility(ESlateVisibility::Visible);
			if (Frame.BirthState == TEXT("unknown") || Frame.BirthState == TEXT("lapsed"))
			{
				CrossWord->SetText(FText::FromString(TEXT("knocking at the world…")));
				CrossWord->SetColorAndOpacity(FSlateColor(Faded));
				// KNOCK AGAIN UNTIL THE WORLD ANSWERS. Every four seconds, not
				// every frame: the bridge is happy to be asked each interval,
				// but sixty times a second is a flood and this is a door, not
				// a race. The state leaving `unknown` is what stops it.
				const double Now = FPlatformTime::Seconds();
				if (Bridge && Now - KnockedAt > 4.0)
				{
					KnockedAt = Now;
					Bridge->EnterWorld();
				}
			}
			else if (Frame.BirthState == TEXT("waiting"))
			{
				KnockedAt = FPlatformTime::Seconds();
				const int32 Left = FMath::Max(0, Frame.BirthRipeAt - Frame.BirthWaited);
				CrossWord->SetText(FText::FromString(FString::Printf(
					TEXT("the world opens in %dm %02ds"), Left / 60, Left % 60)));
				CrossWord->SetColorAndOpacity(FSlateColor(Faded));
			}
			else if (Frame.BirthState == TEXT("ripe"))
			{
				CrossWord->SetText(FText::FromString(
					TEXT("the wait is up, cross into the world")));
				CrossWord->SetColorAndOpacity(FSlateColor(Gilt));
			}
			else
			{
				CrossWord->SetText(FText::FromString(TEXT("waiting on the world")));
				CrossWord->SetColorAndOpacity(FSlateColor(Faded));
			}
		}
	}

	FillVault();
	FillTrade();
	FillCrafts();
	FillHands();
	FillDeath(Delta);

	if (Hereabouts && WherePlate)
	{
		// EMPTY MEANS NOWHERE NAMED, and an empty plate is worse than none.
		// The generator names most of the island but not all of it, and open
		// country between two places is honestly nameless.
		if (Frame.Place.IsEmpty())
		{
			WherePlate->SetVisibility(ESlateVisibility::Collapsed);
		}
		else
		{
			WherePlate->SetVisibility(ESlateVisibility::HitTestInvisible);
			Hereabouts->SetText(FText::FromString(Frame.Place));
		}
	}

	// AND THE OPEN SHEET, on the same beat. What is worn and what is known
	// change when the world says they do and not in between.
	if (OpenTab >= 0)
	{
		FillSheet();
	}
}

// ---------------------------------------------------------------------------

AIntervalHud::AIntervalHud()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AIntervalHud::BeginPlay()
{
	Super::BeginPlay();
	APlayerController* Who = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!Who)
	{
		return;   // Simulate has none; every photograph is taken there.
	}
	UIntervalBridgeSubsystem* Found = GetGameInstance()
		? GetGameInstance()->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	TActorIterator<AIntervalHand> It(GetWorld());
	Hand = It ? *It : nullptr;

	Widget = CreateWidget<UIntervalHudWidget>(Who, UIntervalHudWidget::StaticClass());
	if (!Widget)
	{
		return;
	}
	Widget->Bridge = Found;
	Widget->Hand = Hand;
	Widget->AddToViewport(-5);
	// The map is built during RebuildWidget, which runs inside AddToViewport
	// and therefore BEFORE the two lines above on a first construction. Handed
	// them again here so it is never left with a null bridge.
	if (Widget->Map)
	{
		Widget->Map->Bridge = Found;
		Widget->Map->Hand = Hand;
	}
	if (Found)
	{
		Found->OnChat.AddDynamic(Widget, &UIntervalHudWidget::Heard);
		Found->OnCry.AddDynamic(Widget, &UIntervalHudWidget::Cried);
	}
	if (Hand)
	{
		Hand->OnFeedLine.AddDynamic(Widget, &UIntervalHudWidget::Told);
	}

	// AND THE RIGHT-CLICK MENU, which belongs with the rest of the interface.
	// It is added ABOVE the HUD -- a menu drawn behind the pack is a menu
	// nobody can click.
	Menu = CreateWidget<UIntervalMenuWidget>(Who, UIntervalMenuWidget::StaticClass());
	if (Menu)
	{
		Menu->Hand = Hand;
		Menu->Bridge = Found;
		Menu->AddToViewport(10);
		if (Hand)
		{
			Hand->OnOptions.AddDynamic(Menu, &UIntervalMenuWidget::Offer);
		}
	}
}

void AIntervalHud::EndPlay(const EEndPlayReason::Type Reason)
{
	if (Menu)
	{
		if (Hand)
		{
			Hand->OnOptions.RemoveDynamic(Menu, &UIntervalMenuWidget::Offer);
		}
		Menu->RemoveFromParent();
		Menu = nullptr;
	}
	if (Widget)
	{
		if (UIntervalBridgeSubsystem* Found = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr)
		{
			Found->OnChat.RemoveDynamic(Widget, &UIntervalHudWidget::Heard);
			Found->OnCry.RemoveDynamic(Widget, &UIntervalHudWidget::Cried);
		}
		if (Hand)
		{
			Hand->OnFeedLine.RemoveDynamic(Widget, &UIntervalHudWidget::Told);
		}
		Widget->RemoveFromParent();
		Widget = nullptr;
	}
	Super::EndPlay(Reason);
}
