// Copyright interval.

#include "IntervalGate.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalCitizens.h"
#include "Kismet/GameplayStatics.h"
#include "IntervalGeometry.h"
#include "IntervalLook.h"
#include "Blueprint/WidgetTree.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "Components/Border.h"
#include "Components/PostProcessComponent.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/Overlay.h"
#include "Components/SizeBox.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalGate, Log, All);

// NAMED, NOT ANONYMOUS: see the note in IntervalDoor.cpp. Two anonymous
// namespaces in one unity blob are one namespace, and both files name a
// colour Ink and a colour Quiet.
namespace GatePalette
{
	// The flat window's own plate, read off its stylesheet rather than
	// invented: warm ink on cold stone, and one accent that is firelight.
	// ---- THE GOLD ----
	//
	// The same gold the cursor is cast in, and for the same reason: it is the
	// one colour this window uses to mean "this is the thing". It began as the
	// metal on the pointer and became the thread through everything -- the
	// title over the world, the count on a stack of arrows, the heading on a
	// sheet -- so that the whole interface reads as one made object rather
	// than as a set of panels that happen to be next to each other.
	//
	// Kept beside the ink rather than instead of it: body text stays tallow,
	// because a page of gold is a page nobody can read.
	const FLinearColor Gold(0.839f, 0.659f, 0.290f, 1.f);
	const FLinearColor Ink(0.90f, 0.87f, 0.78f, 1.f);
	const FLinearColor Quiet(0.55f, 0.52f, 0.46f, 1.f);
	const FLinearColor Ember(0.86f, 0.55f, 0.26f, 1.f);
	const FLinearColor Stone(0.055f, 0.055f, 0.06f, 0.88f);
	const FLinearColor Dusk(0.f, 0.f, 0.f, 0.45f);

	// A hairline in ember, above and below the title. One line of one pixel is
	// most of the difference between type on a screenshot and a title card.
	UWidget* RuleIn(UWidgetTree* Tree, UVerticalBox* Box, float Wide, float Below)
	{
		// A SIZE BOX, because an empty Border has no size. Padding alone made
		// a rule that was laid out, animated, and one pixel of nothing: the
		// first card had two invisible hairlines on it.
		USizeBox* Hold = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Hold->SetWidthOverride(Wide);
		Hold->SetHeightOverride(2.f);
		UBorder* Bar = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Bar->SetBrushColor(FLinearColor(0.80f, 0.47f, 0.18f, 0.75f));
		Bar->SetPadding(FMargin(0.f));
		Hold->AddChild(Bar);
		if (UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Hold))
		{
			Slot->SetPadding(FMargin(0.f, 0.f, 0.f, Below));
			Slot->SetHorizontalAlignment(HAlign_Center);
		}
		return Hold;
	}

	UTextBlock* Line(UWidgetTree* Tree, UVerticalBox* Box, const FString& Text,
		const FLinearColor& Colour, int32 Size, float Below, float Track = 0.f)
	{
		UTextBlock* Row = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Row->SetText(FText::FromString(Text));
		Row->SetColorAndOpacity(FSlateColor(Colour));
		FSlateFontInfo Font = Row->GetFont();
		Font.Size = Size;
		Font.LetterSpacing = static_cast<int32>(Track);
		Row->SetFont(Font);
		Row->SetJustification(ETextJustify::Center);
		if (UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Row))
		{
			Slot->SetPadding(FMargin(0.f, 0.f, 0.f, Below));
			Slot->SetHorizontalAlignment(HAlign_Center);
		}
		return Row;
	}
}
using namespace GatePalette;

// ---------------------------------------------------------------------------

TSharedRef<SWidget> UIntervalGateWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		// NOT A BOX ON TOP OF A GAME. The flat window draws a stone panel
		// because it is a flat window and has nothing else to draw with; this
		// one has a camera, a depth of field and a sky, so the plate is a
		// TITLE CARD over a living shot -- letterboxed, with the words sitting
		// on the picture rather than on a slab laid over it.
		UOverlay* Screen = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), TEXT("GateScreen"));

		// A wash, barely there, so type on a bright sky still reads.
		UBorder* Wash = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("GateWash"));
		Wash->SetBrushColor(FLinearColor(0.01f, 0.012f, 0.015f, 0.24f));
		if (UOverlaySlot* Slot = Screen->AddChildToOverlay(Wash))
		{
			Slot->SetHorizontalAlignment(HAlign_Fill);
			Slot->SetVerticalAlignment(VAlign_Fill);
		}

		// ---- THE BARS ----
		// Two black bands, and they do more work than anything else here: a
		// letterbox is the oldest signal there is for "this is a picture, and
		// it is about to begin".
		TopBar = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("GateTop"));
		TopBar->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 1.f));
		TopBar->SetPadding(FMargin(0.f, 46.f));
		if (UOverlaySlot* Slot = Screen->AddChildToOverlay(TopBar))
		{
			Slot->SetHorizontalAlignment(HAlign_Fill);
			Slot->SetVerticalAlignment(VAlign_Top);
		}
		FootBar = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("GateFoot"));
		FootBar->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 1.f));
		FootBar->SetPadding(FMargin(0.f, 46.f));
		if (UOverlaySlot* Slot = Screen->AddChildToOverlay(FootBar))
		{
			Slot->SetHorizontalAlignment(HAlign_Fill);
			Slot->SetVerticalAlignment(VAlign_Bottom);
		}

		UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("GateBox"));
		if (UOverlaySlot* Slot = Screen->AddChildToOverlay(Box))
		{
			Slot->SetHorizontalAlignment(HAlign_Center);
			Slot->SetVerticalAlignment(VAlign_Center);
		}

		// ---- THE WORDS ----
		Rising.Add(RuleIn(WidgetTree, Box, 240.f, 10.f));
		// THE TITLE IS THE GOLD. It was the same tallow as the lines under it,
		// which made the card read as a paragraph with a big first line.
		Rising.Add(Line(WidgetTree, Box, TEXT("INTERVAL"), Gold, 96, 2.f, 26.f));
		Rising.Add(RuleIn(WidgetTree, Box, 360.f, 16.f));
		Rising.Add(Line(WidgetTree, Box,
			TEXT("a world that runs on rules, not servers"), Quiet, 15, 3.f, 2.f));
		Rising.Add(Line(WidgetTree, Box, TEXT("THE UNREAL WINDOW"), Ember, 10, 40.f, 8.f));

		StatusRow = Line(WidgetTree, Box, TEXT("waking the world…"), Ink, 15, 5.f, 1.f);
		Rising.Add(StatusRow);
		// WHAT THE DOOR KNOWS, on the door. A window that opens on a number
		// climbing and a finalized number that is not is a window that should
		// say so before you walk in, not after.
		StandingRow = Line(WidgetTree, Box, TEXT(""), Quiet, 11, 4.f, 1.f);
		Rising.Add(StandingRow);
		KeyRow = Line(WidgetTree, Box, TEXT(""), Quiet, 10, 34.f, 1.f);
		Rising.Add(KeyRow);

		// ---- AND THE TWO WAYS A CITIZEN CROSSES BETWEEN WINDOWS ----
		//
		// Small, quiet and under the line that already says where the citizen
		// lives, because this is not the thing most people came to do. It is
		// the thing that matters enormously to the one person who started in
		// the browser last week and has just downloaded this.
		//
		// A plain text pair rather than two more buttons the size of ENTER:
		// the card has one call to action and adding two more would leave a
		// newcomer choosing between three doors on their first screen.
		{
			UHorizontalBox* Pair = WidgetTree->ConstructWidget<UHorizontalBox>(
				UHorizontalBox::StaticClass());
			auto Small = [&](const TCHAR* Text) -> UButton*
			{
				UButton* B = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
				FButtonStyle St = B->GetStyle();
				St.Normal.TintColor = FSlateColor(FLinearColor(0.02f, 0.02f, 0.025f, 0.40f));
				St.Hovered.TintColor = FSlateColor(FLinearColor(0.26f, 0.15f, 0.05f, 0.70f));
				St.Pressed.TintColor = FSlateColor(FLinearColor(0.40f, 0.22f, 0.07f, 0.85f));
				St.NormalPadding = FMargin(0.f);
				St.PressedPadding = FMargin(0.f);
				B->SetStyle(St);
				UTextBlock* L = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
				L->SetText(FText::FromString(Text));
				L->SetColorAndOpacity(FSlateColor(Quiet));
				FSlateFontInfo F = L->GetFont();
				F.Size = 10;
				F.LetterSpacing = 3;
				L->SetFont(F);
				if (UButtonSlot* Sl = Cast<UButtonSlot>(B->AddChild(L)))
				{
					Sl->SetPadding(FMargin(14.f, 6.f, 14.f, 6.f));
					Sl->SetHorizontalAlignment(HAlign_Center);
				}
				Pair->AddChildToHorizontalBox(B);
				return B;
			};
			CarryInButton = Small(TEXT("BRING A CITIZEN IN"));
			CarryOutButton = Small(TEXT("CARRY THIS ONE OUT"));
			CarryInButton->OnClicked.AddDynamic(this, &UIntervalGateWidget::OnCarryIn);
			CarryOutButton->OnClicked.AddDynamic(this, &UIntervalGateWidget::OnCarryOut);
			if (UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Pair))
			{
				Slot->SetHorizontalAlignment(HAlign_Center);
				Slot->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f));
			}
			Rising.Add(Pair);
		}

		// what the bridge said about the last one, in the same quiet hand
		CarryRow = Line(WidgetTree, Box, TEXT(""), Quiet, 10, 10.f, 1.f);
		Rising.Add(CarryRow);

		// ---- THE BUTTON ----
		// An outline, not a slab: the default Slate button is a grey pill and
		// it is the one thing that would say "editor" on an otherwise finished
		// picture. A thin ember border with the world showing through it says
		// door.
		UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("GateFrame"));
		Frame->SetBrushColor(FLinearColor(0.72f, 0.42f, 0.16f, 0.85f));
		Frame->SetPadding(FMargin(1.5f));
		if (UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Frame))
		{
			Slot->SetHorizontalAlignment(HAlign_Center);
		}
		Rising.Add(Frame);

		EnterButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("GateEnter"));
		FButtonStyle Style = EnterButton->GetStyle();
		Style.Normal.TintColor = FSlateColor(FLinearColor(0.02f, 0.02f, 0.025f, 0.72f));
		Style.Hovered.TintColor = FSlateColor(FLinearColor(0.30f, 0.17f, 0.06f, 0.88f));
		Style.Pressed.TintColor = FSlateColor(FLinearColor(0.46f, 0.26f, 0.08f, 0.95f));
		Style.NormalPadding = FMargin(0.f);
		Style.PressedPadding = FMargin(0.f);
		EnterButton->SetStyle(Style);
		EnterButton->OnClicked.AddDynamic(this, &UIntervalGateWidget::OnEnter);
		Frame->SetContent(EnterButton);

		EnterLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		EnterLabel->SetText(FText::FromString(TEXT("…")));
		EnterLabel->SetColorAndOpacity(FSlateColor(Ember));
		{
			FSlateFontInfo Font = EnterLabel->GetFont();
			Font.Size = 17;
			Font.LetterSpacing = 9;
			EnterLabel->SetFont(Font);
			EnterLabel->SetJustification(ETextJustify::Center);
		}
		if (UButtonSlot* Slot = Cast<UButtonSlot>(EnterButton->AddChild(EnterLabel)))
		{
			Slot->SetPadding(FMargin(46.f, 15.f, 38.f, 15.f));
			Slot->SetHorizontalAlignment(HAlign_Center);
		}

		WidgetTree->RootWidget = Screen;
	}
	return Super::RebuildWidget();
}

void UIntervalGateWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
	Super::NativeTick(Geometry, DeltaSeconds);
	if (!StatusRow)
	{
		return;
	}

	// ---- IT ARRIVES, IT DOES NOT APPEAR ----
	// The bars come in first and the words follow them, over about two
	// seconds. A title card that is simply THERE on the first frame reads as
	// a menu; one that arrives reads as a film starting, and the difference
	// costs eight lines.
	Age += DeltaSeconds;
	const float Bars = FMath::Clamp(Age / 0.75f, 0.f, 1.f);
	const float Words = FMath::Clamp((Age - 0.45f) / 1.25f, 0.f, 1.f);
	const float Eased = Words * Words * (3.f - 2.f * Words);
	if (TopBar) { TopBar->SetRenderTranslation(FVector2D(0.f, -46.f * (1.f - Bars))); }
	if (FootBar) { FootBar->SetRenderTranslation(FVector2D(0.f, 46.f * (1.f - Bars))); }
	for (const TObjectPtr<UWidget>& W : Rising)
	{
		if (!W) { continue; }
		W->SetRenderOpacity(Eased);
		W->SetRenderTranslation(FVector2D(0.f, 14.f * (1.f - Eased)));
	}

	// THE BUTTON IS DISABLED UNTIL THERE IS SOMEWHERE TO GO. A gate that lets
	// you in before the bridge has found the world drops you into an empty
	// island and looks broken; saying "waking the world" for two seconds is
	// the honest version of the same wait.
	const bool bReady = Bridge && Bridge->IsConnected() && Bridge->GetFrame().bHasMe;
	if (EnterButton)
	{
		EnterButton->SetIsEnabled(bReady);
	}

	// AND THE CARD KEEPS THE KEYBOARD.
	//
	// `NativeConstruct` takes focus once, and once is not enough: the card is
	// built before the bridge has answered, and in the seconds between then
	// and `bReady` anything that touches the viewport -- a click on the world
	// behind, the editor restoring focus after a PIE start -- takes it away
	// again. The key handler below then receives nothing, the button cannot
	// be reached by automation at all (the PIE viewport's UMG is not in the
	// editor's Slate tree), and the card sits there looking hung.
	//
	// Asked for every frame the card is up, which is a handful of frames and
	// costs nothing, and only while it is still waiting for a press.
	if (APlayerController* PC = GetOwningPlayer())
	{
		if (!HasUserFocus(PC))
		{
			SetUserFocus(PC);
		}
	}

	if (!Bridge || !Bridge->IsConnected())
	{
		StatusRow->SetText(FText::FromString(TEXT("no bridge: start unreal-bridge.mjs")));
		StatusRow->SetColorAndOpacity(FSlateColor(Ember));
		if (EnterLabel) { EnterLabel->SetText(FText::FromString(TEXT("…"))); }
		return;
	}
	StatusRow->SetColorAndOpacity(FSlateColor(Ink));

	const FIntervalFrame& Frame = Bridge->GetFrame();
	const FString WorldId = Bridge->GetWorldId();
	if (!bReady)
	{
		StatusRow->SetText(FText::FromString(FString::Printf(
			TEXT("waking %s… interval %lld"), *WorldId.Left(10), Frame.Tick)));
		if (EnterLabel) { EnterLabel->SetText(FText::FromString(TEXT("…"))); }
		return;
	}

	// ---- NOUGHT IS NOT THE WORLD, AND THE CARD SAID IT WAS ----
	//
	// Before you cross, the bridge is ticking a PRACTICE of the island: a
	// different world by id, started at tick 1, on its own timer. The card
	// printed that tick beside the real world's name and the real world's
	// finalized height, so it read
	//
	//     246612f9a1, interval 1 ... -157633 behind
	//
	// which is three true numbers making one false statement. Nothing was
	// behind: one figure was the practice world's clock and the other was the
	// country's, and subtracting them measures nothing at all.
	if (Frame.bNought)
	{
		StatusRow->SetText(FText::FromString(FString::Printf(
			TEXT("Nought,  a practice of the world,  interval %lld"), Frame.Tick)));
	}
	else
	{
		StatusRow->SetText(FText::FromString(FString::Printf(
			TEXT("%s,  interval %lld"), *WorldId.Left(10), Frame.Tick)));
	}
	if (StandingRow)
	{
		int32 W = 0, H = 0;
		Bridge->GetWorldSize(W, H);
		// AND NOUGHT HAS NO WITNESSES AND NOTHING TO BE BEHIND. Nothing there
		// is recorded and nothing is finalized, so a quorum and a height are
		// the country's facts, not this island's. Saying what it IS beats
		// printing three numbers that belong to somewhere else.
		if (Frame.bNought)
		{
			StandingRow->SetText(FText::FromString(FString::Printf(
				TEXT("%d × %d tiles,  nothing here is recorded"), W, H)));
			StandingRow->SetColorAndOpacity(FSlateColor(Quiet));
		}
		else
		{
			const int64 Behind = Frame.Tick - Frame.FinalizedTick;
			StandingRow->SetText(FText::FromString(FString::Printf(
				TEXT("%d × %d tiles,  %d of %d witnesses,  %lld behind"),
				W, H, Frame.Witnesses, Frame.Quorum, Behind)));
			StandingRow->SetColorAndOpacity(FSlateColor(Behind > 5 ? Ember : Quiet));
		}
	}
	if (KeyRow)
	{
		// WHERE THE CITIZEN IS, not what it says. See the header.
		const FString Where = Bridge->GetKeyFile();
		KeyRow->SetText(FText::FromString(Where.IsEmpty()
			? FString(TEXT("the bridge holds the key"))
			: FString::Printf(TEXT("the bridge holds the key: %s"), *Where)));
	}
	if (CarryRow)
	{
		// Empty until somebody asks for something, so the card is not carrying
		// a blank row of explanation nobody wanted.
		CarryRow->SetText(FText::FromString(Bridge->CarrySaid));
		// This card's palette is Ink, Quiet and Ember; there is no warning
		// colour on it, and inventing one for two lines would put a fourth
		// hand on a screen whose whole character is that it has three. A
		// refusal is Ink: brighter than quiet, and it reads as a thing said
		// rather than a thing gone wrong, which is what a refusal here is.
		CarryRow->SetColorAndOpacity(FSlateColor(
			Bridge->CarrySaid.IsEmpty() ? Quiet : (Bridge->bCarryWorked ? Ember : Ink)));
	}
	if (EnterLabel)
	{
		EnterLabel->SetText(FText::FromString(TEXT("ENTER THE WORLD")));
		// BREATHING, not blinking. Something on a still card has to move or
		// the eye decides the picture is frozen and stops looking at it.
		const float Pulse = 0.78f + 0.22f * (0.5f + 0.5f * FMath::Sin(Age * 2.1f));
		EnterLabel->SetColorAndOpacity(FSlateColor(Ember * Pulse));
	}
}

void UIntervalGateWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// So the key below reaches this and not the world behind it.
	SetIsFocusable(true);
	// AND SO THE PRESS DOES TOO. A UUserWidget is SelfHitTestInvisible by
	// default: its children are hit-tested and the widget itself is not, so
	// `NativeOnMouseButtonDown` on the card would never once have been called.
	// Visible makes the whole card a target, which is what it should be, and
	// the button underneath still gets first refusal on a press that lands on
	// it.
	SetVisibility(ESlateVisibility::Visible);
	if (APlayerController* PC = GetOwningPlayer())
	{
		SetUserFocus(PC);
	}
}

FReply UIntervalGateWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Key)
{
	const FKey Pressed = Key.GetKey();
	const bool bReady = Bridge && Bridge->IsConnected() && Bridge->GetFrame().bHasMe;
	if (bReady && (Pressed == EKeys::Enter || Pressed == EKeys::SpaceBar))
	{
		OnEnter();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(Geometry, Key);
}

FReply UIntervalGateWidget::NativeOnMouseButtonDown(const FGeometry& Geometry,
	const FPointerEvent& Mouse)
{
	const bool bReady = Bridge && Bridge->IsConnected() && Bridge->GetFrame().bHasMe;
	if (bReady && Mouse.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		OnEnter();
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(Geometry, Mouse);
}

void UIntervalGateWidget::OnEnter()
{
	if (Gate)
	{
		Gate->Enter();
	}
}

void UIntervalGateWidget::OnCarryOut()
{
	if (Bridge)
	{
		Bridge->CarryCitizenOut();
	}
}

void UIntervalGateWidget::OnCarryIn()
{
	if (Bridge)
	{
		Bridge->CarryCitizenIn();
	}
}

// ---------------------------------------------------------------------------

AIntervalGate::AIntervalGate()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AIntervalGate::BeginPlay()
{
	Super::BeginPlay();

	// NOT IN SIMULATE. There is no player controller there, which is exactly
	// the mode every screenshot in this project is taken in.
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC)
	{
		return;
	}
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);

	if (const UGameInstance* GI = GetGameInstance())
	{
		Bridge = GI->GetSubsystem<UIntervalBridgeSubsystem>();
	}

	// ---- THE CAMERA COMES FIRST, AND IT IS NOT PART OF THE DOOR ----
	//
	// This used to return here when a level turned `bGate` off, which took the
	// WATCH CAMERA away with the title card -- and the watch camera is the
	// whole window. What was left was the third-person template's mannequin
	// standing on a blue disc at the world origin, eighty metres from any of
	// the country this project spent months drawing, and the window looked
	// like an empty Unreal project.
	//
	// A door is a thing you pass through. The window is what is on the other
	// side of it, and it exists whether or not anybody was shown a door.
	Eye = GetWorld()->SpawnActor<ACameraActor>();
	if (Eye)
	{
		WasWatching = PC->GetViewTarget();
		PC->SetViewTargetWithBlend(Eye, 0.f);
		// Put it where it belongs immediately rather than letting it lerp in
		// from the origin, which is a two-second swoop across the island.
		const FVector Look = Heart();
		const float Reach = Wardrobe ? Wardrobe->WatchReach : 1250.f;
		const float Rise = Wardrobe ? Wardrobe->WatchRise : 820.f;
		const float Rad = FMath::DegreesToRadians(Wardrobe ? Wardrobe->WatchBearing : 218.7f);
		// The wheel scales the whole triangle -- out AND up -- so the angle of
		// the shot never changes and zooming out does not slowly turn a
		// three-quarter view into a flat overhead one.
		const FVector Want = Look + FVector(FMath::Cos(Rad) * Reach * Pull,
			FMath::Sin(Rad) * Reach * Pull, Rise * Pull);
		Eye->SetActorLocation(Want);
		Eye->SetActorRotation((Look - Want).Rotation());
	}

	if (Wardrobe && !Wardrobe->bGate)
	{
		// No title card, no glass, no theme -- but watching, which is the
		// point. `bWaiting` stays false, so Tick goes straight to following
		// the citizen.
		return;
	}

	// ---- THE GLASS ----
	// Over the air's own grade, at a priority above it, and gone again the
	// moment the gate opens. Depth of field is what makes this a title card
	// rather than a menu: the words are the near thing and the country is the
	// far one, and nobody has to be told.
	Glass = NewObject<UPostProcessComponent>(this);
	Glass->SetupAttachment(RootComponent);
	Glass->bUnbound = true;
	Glass->Priority = 20.f;
	{
		FPostProcessSettings& G = Glass->Settings;
		G.bOverride_DepthOfFieldFocalDistance = true;
		G.DepthOfFieldFocalDistance = 320.f;     // well in front of anything
		G.bOverride_DepthOfFieldFstop = true;
		G.DepthOfFieldFstop = 1.1f;
		G.bOverride_DepthOfFieldDepthBlurAmount = true;
		G.DepthOfFieldDepthBlurAmount = 0.75f;
		G.bOverride_VignetteIntensity = true;
		G.VignetteIntensity = 0.72f;
		G.bOverride_ColorSaturation = true;
		G.ColorSaturation = FVector4(0.84f, 0.84f, 0.84f, 1.f);
		G.bOverride_ColorContrast = true;
		G.ColorContrast = FVector4(1.06f, 1.06f, 1.06f, 1.f);
	}
	Glass->RegisterComponent();

	Plate = CreateWidget<UIntervalGateWidget>(PC, UIntervalGateWidget::StaticClass());
	if (Plate)
	{
		Plate->Bridge = Bridge;
		Plate->Gate = this;
		Plate->AddToViewport(1000);
	}
	PC->SetShowMouseCursor(true);
	FInputModeUIOnly Mode;
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	PC->SetInputMode(Mode);

	if (Wardrobe && Wardrobe->GateTheme)
	{
		Theme = UGameplayStatics::SpawnSound2D(this, Wardrobe->GateTheme, 1.f, 1.f, 0.f, nullptr, true);
	}
	bWaiting = true;
	// SAY WHETHER THE THEME STARTED. "Is there music?" is a question nobody
	// can answer from a screenshot, and a sound that silently failed to spawn
	// looks exactly like a sound that is playing on a muted machine.
	UE_LOG(LogIntervalGate, Log, TEXT("[interval] the gate is up: theme %s, %s"),
		(Wardrobe && Wardrobe->GateTheme) ? *Wardrobe->GateTheme->GetName() : TEXT("NONE"),
		Theme ? TEXT("playing") : TEXT("DID NOT START"));
}

FVector AIntervalGate::Heart() const
{
	if (Bridge)
	{
		const FIntervalFrame& Frame = Bridge->GetFrame();
		if (Frame.bHasMe)
		{
			// WHERE THE CITIZEN IS DRAWN, not which tile the world says they
			// are on. The tile moves a whole two metres at once, once an
			// interval; easing a camera toward that makes it lurch and settle
			// on every tick for the whole of a walk, beside a body that is
			// gliding. See AIntervalCitizens::LastDrawnAt.
			if (!Drawn.IsValid())
			{
				if (const UWorld* W = GetWorld())
				{
					const_cast<AIntervalGate*>(this)->Drawn = Cast<AIntervalCitizens>(
						UGameplayStatics::GetActorOfClass(W, AIntervalCitizens::StaticClass()));
				}
			}
			{
				if (AIntervalCitizens* Body = Drawn.Get())
				{
					FVector Seen;
					if (Body->LastDrawnAt(Bridge->GetPlayerId(), Seen))
					{
						// THE GROUND THEY STAND ON, WHICH IS NOT SEA LEVEL.
						//
						// This line read `Seen.Z = 0.f`, and it was right for
						// exactly as long as the island was flat. The window
						// draws the generator's own elevation field now, so a
						// citizen standing in a settlement four metres below
						// sea level -- which most of Anchor is -- was watched
						// from a camera aimed four metres over their head.
						//
						// The symptoms did not look like a camera fault, which
						// is why it took this long: the figure sat low in the
						// frame and small, the floor they were standing on
						// filled the middle of the picture, and indoors the
						// wall behind them came up past their head. It was
						// reported as "idk what it centers but it feels weird"
						// and then, later and more exactly, as not being able
						// to see your own character inside a building.
						//
						// `LastDrawnAt` gives the drawn body's position, whose
						// origin is the feet, so this is already the ground.
						// Nothing needs subtracting; the old line was throwing
						// the terrain away.
						return Seen;
					}
				}
			}
			return UIntervalGeometry::TileToWorld(Frame.Me.X, Frame.Me.Y);
		}
		int32 W = 0, H = 0;
		Bridge->GetWorldSize(W, H);
		if (W > 0 && H > 0)
		{
			return UIntervalGeometry::TileToWorld(W / 2, H / 2);
		}
	}
	return FVector::ZeroVector;
}

void AIntervalGate::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// ---- THE GLASS BELONGS TO THE CARD AND MUST NOT OUTLIVE IT ----
	//
	// `Glass` is a post-process the title card is read through: sixteen per
	// cent of the colour taken out, a heavy vignette and a depth blur. Over a
	// card that is composition. Over the WORLD it is a grey, soft, lifeless
	// version of a place that is none of those things, and the difference
	// between the editor's view of this island and the window's turned out to
	// be mostly this.
	//
	// It was torn down in exactly one place, `Enter()`, which cannot run until
	// `bHasMe` is true. So any path that takes the card away without a citizen
	// existing left the glass over everything, and the longest such path is
	// the one every new player walks: five minutes of the vigil, which is a
	// first impression of this world seen through frosted glass.
	//
	// Belt and braces rather than a second teardown: the glass simply may not
	// exist without the card. Whatever removes the card, by whatever route,
	// takes the glass with it.
	if (Glass && !Plate)
	{
		Glass->DestroyComponent();
		Glass = nullptr;
	}

	if (!Eye)
	{
		return;
	}
	if (!bWaiting)
	{
		// ---- WATCHING ----
		// The same camera, no longer going round. It settles at a fixed
		// bearing off the citizen and follows them, lazily, for ever.
		const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);
		float Reach = Wardrobe ? Wardrobe->WatchReach : 1250.f;
		float Rise = Wardrobe ? Wardrobe->WatchRise : 820.f;
		// ---- OR THE ANGLE, WHICH IS THE THING ANYBODY WANTS TO TURN ----
		//
		// See `WatchPitch`. The slant is kept, so the camera stands exactly as
		// far from the citizen as it did and only the angle moves. Changing
		// the height alone would tilt it AND pull it in, which is two changes
		// wearing one name and is how the first attempt at this went wrong.
		//
		// AND THE ANGLE COMES FROM HOW MUCH SKY IS WANTED, not the other way
		// about. See `SkyShare`: an angle does not decide how much sky is in
		// frame, the vertical field does, and that depends on the shape of the
		// window -- the same twenty-four degrees gave a band of sky on a 16:9
		// window and none at all on a wide one, with the horizon exactly on
		// the top edge. The field is asked for rather than assumed.
		float Down = -1.f;
		if (Wardrobe && Wardrobe->WatchPitch >= 0.f)
		{
			Down = FMath::Clamp(Wardrobe->WatchPitch, 1.f, 89.f);
		}
		else if (Wardrobe && Eye->GetCameraComponent())
		{
			// THE VIEWPORT'S OWN SHAPE. The controller above is scoped to the
			// input block; this is the same question asked of the engine,
			// which answers it whether or not anybody is holding a keyboard.
			int32 Wide = 0, Tall = 0;
			if (const APlayerController* Seat =
				UGameplayStatics::GetPlayerController(this, 0))
			{
				Seat->GetViewportSize(Wide, Tall);
			}
			if (Wide > 0 && Tall > 0)
			{
				const float Across = FMath::DegreesToRadians(
					Eye->GetCameraComponent()->FieldOfView * 0.5f);
				const float Aspect = static_cast<float>(Wide) / static_cast<float>(Tall);
				const float Up = 2.f * FMath::RadiansToDegrees(
					FMath::Atan(FMath::Tan(Across) / FMath::Max(Aspect, 0.1f)));
				// The horizon sits `SkyShare` of the way down the frame, and
				// the frame runs from pitch + half the field to pitch minus
				// it. One line of algebra, and the sign is the camera looking
				// DOWN.
				Down = FMath::Clamp(
					Up * (0.5f - FMath::Clamp(Wardrobe->SkyShare, 0.f, 0.5f)),
					1.f, 89.f);
			}
		}
		if (Down > 0.f)
		{
			const float Slant = FMath::Sqrt(Reach * Reach + Rise * Rise);
			const float Rad2 = FMath::DegreesToRadians(Down);
			Reach = Slant * FMath::Cos(Rad2);
			Rise = Slant * FMath::Sin(Rad2);
		}
		// ---- AND THE PLAYER MAY TURN IT ----
		//
		// The camera sat at one fixed bearing for ever, which is fine for a
		// photograph and wrong for playing: a citizen could see about a dozen
		// tiles in one direction and had no way to look round a building, or
		// to see what was behind them, or to aim a walk at ground the camera
		// happened not to be pointing at. Asked for in those words -- "maybe
		// the ability to rotate the screen so you can look around and easier
		// be able to walk further as well".
		//
		// Left and right, or Q and E, the way this genre has always done it.
		// It is a WINDOW's control and not a deed: nothing is filed, the world
		// is not told, and a citizen who turns their camera has not moved.
		if (const APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			const bool bLeft = PC->IsInputKeyDown(EKeys::Left)
				|| PC->IsInputKeyDown(EKeys::Q);
			const bool bRight = PC->IsInputKeyDown(EKeys::Right)
				|| PC->IsInputKeyDown(EKeys::E);
			if (bLeft != bRight)
			{
				Spin += (bRight ? 1.f : -1.f) * SpinRate * DeltaSeconds;
				Spin = FMath::Fmod(Spin, 360.f);
			}

			// ---- AND IN AND OUT, ON THE WHEEL ----
			//
			// Turning let a citizen look around a building; it did not let
			// them see further, and on a top-down view the amount of world on
			// screen is the difference between planning a walk and taking it
			// one tile at a time. So the wheel pulls the camera back and
			// pushes it in, which is what a hand on a mouse expects it to do.
			//
			// A LITTLE, on purpose. Too far out and this stops being a view of
			// a person and becomes the minimap, which already exists and is
			// better at it; too far in and the camera is inside the roof. The
			// bounds are a third under and two thirds over the wardrobe's own
			// distance, so the shot the world was framed for is the middle of
			// the range and the default.
			// ---- AND THE WAY EVERYBODY ACTUALLY TRIES FIRST ----
			//
			// Q and E turn the camera and always have. Nobody found them:
			// "how do i rotate the camera? I tried arrows and holding in mouse
			// click and drag but nothing happened." Holding a button and
			// dragging is what a hand reaches for, and a control nobody
			// reaches for is a control that does not exist.
			//
			// The RIGHT button, which is the one this genre turns with. It
			// already opens the menu, and the two do not collide because a
			// menu is opened by a right click that does NOT move -- the hand
			// waits for the release and measures the distance. So a flick of
			// the wrist turns the world and a tap still asks what is there.
			const bool bTurning = PC->IsInputKeyDown(EKeys::RightMouseButton);
			const FVector2D Now = FSlateApplication::Get().GetCursorPos();
			if (bTurning)
			{
				if (bDragging)
				{
					// A quarter of a degree a pixel: a comfortable drag across
					// a third of the screen turns a quarter circle.
					Spin = FMath::Fmod(Spin + (Now.X - Dragged.X) * 0.25f, 360.f);
				}
				bDragging = true;
				Dragged = Now;
			}
			else
			{
				bDragging = false;
			}

			// `MouseScrollUp`/`Down` and NOT the analog `MouseWheelAxis`: the
			// axis reads zero unless the project has bound an axis mapping to
			// it, and this window binds nothing -- it reads the keyboard and
			// the mouse straight off the controller. The two notch keys are
			// always there.
			if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp))
			{
				Pull = FMath::Clamp(Pull - 0.09f, 0.66f, 1.7f);
			}
			if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown))
			{
				Pull = FMath::Clamp(Pull + 0.09f, 0.66f, 1.7f);
			}

			// ---- AND THE SAME TWO THINGS WITH FINGERS ----
			//
			// A phone has no second button and no wheel. It has a drag and a
			// pinch, and everybody already knows what those do to a map, so
			// there is nothing to teach and nothing to put on screen.
			float Ax = 0.f, Ay = 0.f, Bx = 0.f, By = 0.f;
			bool bOne = false, bTwo = false;
			PC->GetInputTouchState(ETouchIndex::Touch1, Ax, Ay, bOne);
			PC->GetInputTouchState(ETouchIndex::Touch2, Bx, By, bTwo);

			if (bOne && bTwo)
			{
				// PINCH. The distance between the fingers, as a ratio against
				// last frame, so the zoom is proportional the way a hand
				// expects: the same spread moves the camera the same fraction
				// whether it is close in or far out.
				const float Span = FVector2D::Distance(FVector2D(Ax, Ay), FVector2D(Bx, By));
				if (Pinched > 1.f && Span > 1.f)
				{
					Pull = FMath::Clamp(Pull * (Pinched / Span), 0.66f, 1.7f);
				}
				Pinched = Span;
				// TWO FINGERS ARE NOT A DRAG. Without this the midpoint of a
				// pinch wanders and the world spins while somebody is zooming.
				bSwiping = false;
			}
			else
			{
				Pinched = 0.f;
				if (bOne)
				{
					const FVector2D Now2(Ax, Ay);
					if (bSwiping)
					{
						// The same quarter of a degree a pixel the mouse
						// turns at, so a phone and a desktop feel the same.
						Spin = FMath::Fmod(Spin + (Now2.X - Swiped.X) * 0.25f, 360.f);
					}
					bSwiping = true;
					Swiped = Now2;
				}
				else
				{
					bSwiping = false;
				}
			}
		}
		const float Lag = Wardrobe ? Wardrobe->WatchLag : 2.2f;

		// ---- THE LAG IS ON WHERE IT LOOKS, NOT ON WHERE IT STANDS ----
		//
		// This eased the camera's POSITION toward a point on a circle round
		// the citizen. That is right while somebody walks and wrong the moment
		// anybody turns: the target runs round the circle and a straight-line
		// ease chases it across the CHORD, so the camera cuts the corner and
		// falls inside its own orbit, then drifts back out when the turn
		// stops. Reported exactly as it looks -- "it kind of curves outwards
		// and inwards when rotating instead of staying stable as you rotate
		// the camera around the player."
		//
		// Nothing about the lag was wrong; what was wrong is what it was
		// applied to. Smooth the three things that are actually being asked
		// for -- where to look, which way round, how far out -- and then put
		// the camera exactly on the circle those three describe. A turn is now
		// a turn at a constant radius by construction rather than by luck, and
		// a walk is still followed lazily, because the point it is following
		// is still eased.
		const FVector Look = Heart();
		if (!bWatched)
		{
			Watching = Look;
			Bearing = (Wardrobe ? Wardrobe->WatchBearing : 218.7f) + Spin;
			Pulled = Pull;
			bWatched = true;
		}
		Watching = FMath::VInterpTo(Watching, Look, DeltaSeconds, Lag);
		Pulled = FMath::FInterpTo(Pulled, Pull, DeltaSeconds, Lag * 2.f);

		// THE SHORT WAY ROUND, which an ordinary ease cannot find. `Spin` is
		// wrapped into a full turn, so easing 179 toward -179 takes the camera
		// the whole way round the world rather than two degrees across the
		// join. `UnwindDegrees` puts the difference back in [-180, 180] and
		// the ease is applied to THAT.
		const float WantBearing = (Wardrobe ? Wardrobe->WatchBearing : 218.7f) + Spin;
		const float Off = FMath::UnwindDegrees(WantBearing - Bearing);
		Bearing = FMath::UnwindDegrees(
			Bearing + Off * FMath::Clamp(DeltaSeconds * Lag * 3.2f, 0.f, 1.f));

		const float Rad = FMath::DegreesToRadians(Bearing);
		// The wheel scales the whole triangle -- out AND up -- so the angle of
		// the shot never changes and zooming out does not slowly turn a
		// three-quarter view into a flat overhead one.
		const FVector Where = Watching
			+ FVector(FMath::Cos(Rad) * Reach * Pulled,
				FMath::Sin(Rad) * Reach * Pulled, Rise * Pulled);
		Eye->SetActorLocation(Where);
		// AND IT LOOKS AT THE POINT IT IS STANDING ROUND, exactly. The
		// rotation used to be eased as well, on top of an eased position, so
		// during a turn the camera was both in the wrong place and pointing
		// somewhere else again. Both smoothnesses are in `Watching` and
		// `Bearing` now, and two eases over one motion is a wobble.
		Eye->SetActorRotation((Watching - Where).Rotation());
		return;
	}
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);
	// A LEVEL MAY OPEN IT FROM THE OUTSIDE. Turning `bGate` off while the
	// plate is up takes it down exactly as pressing the button does -- same
	// blend, same fade -- which is how a window with no hands can be shown to
	// work: the PIE viewport's UMG does not appear in the editor's Slate tree,
	// so nothing but a person can press that button.
	if (Wardrobe && !Wardrobe->bGate)
	{
		Enter();
		return;
	}
	const float Reach = Wardrobe ? Wardrobe->GateReach : 4200.f;
	const float Rise = Wardrobe ? Wardrobe->GateRise : 1900.f;
	const float Turn = Wardrobe ? Wardrobe->GateTurn : 2.4f;

	// ROUND, SLOWLY, AND LOOKING AT SOMEBODY. A pan over empty country says
	// less than a pan that keeps a citizen in it: the world is inhabited, and
	// that is the thing this window is for.
	// ROUND AND IN. A pure orbit at a fixed distance reads as a screensaver;
	// creeping closer the whole time it is up reads as a shot. It is a third
	// of the distance over the first half-minute and nobody will ever name it.
	Turned = FMath::Fmod(Turned + Turn * DeltaSeconds, 360.f);
	Waited = FMath::Min(Waited + DeltaSeconds, 30.f);
	const float Creep = FMath::Lerp(1.34f, 1.f, Waited / 30.f);
	const FVector Look = Heart();
	const float Rad = FMath::DegreesToRadians(Turned);
	const FVector Where = Look + FVector(FMath::Cos(Rad) * Reach * Creep,
		FMath::Sin(Rad) * Reach * Creep, Rise * Creep);
	Eye->SetActorLocation(Where);
	Eye->SetActorRotation((Look - Where).Rotation());
}

void AIntervalGate::Enter()
{
	if (!bWaiting)
	{
		return;
	}
	bWaiting = false;
	UE_LOG(LogIntervalGate, Log, TEXT("[interval] the gate opens"));

	if (Plate)
	{
		Plate->RemoveFromParent();
		Plate = nullptr;
	}
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		// THE MOUSE STAYS. This read `SetShowMouseCursor(false)` and
		// `FInputModeGameOnly()` -- the template's idea of "the menu is over,
		// now play" -- and it was wrong twice over for this world.
		//
		// GameOnly routes no mouse event to UMG at all, so crossing the
		// threshold silently disabled every clickable thing this window has:
		// the chat line could not be typed in, the pack slots could not be
		// picked up from, and the right-click menu never opened because the
		// right click never arrived. Everything built for a player to use
		// became reachable only from the automation harness, which is not a
		// way to play; the whole interaction model was unreachable by a human
		// from the first second of the first session onwards. It was found by
		// trying to play the window with a real mouse, and by nothing else --
		// every deed still worked when called directly, so nothing looked
		// broken from the inside.
		//
		// And hiding the cursor is wrong on its own: this is a world entered
		// by pointing at it. A citizen walks by clicking the ground.
		//
		// GameAndUI is the mode that suits it -- widgets get first refusal on
		// a click and the world gets the rest -- with the pointer unlocked,
		// because the window is played in a window.
		PC->SetShowMouseCursor(true);
		PC->bEnableClickEvents = true;
		PC->bEnableMouseOverEvents = true;
		FInputModeGameAndUI Playing;
		Playing.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		Playing.SetHideCursorDuringCapture(false);
		PC->SetInputMode(Playing);
		// THE VIEW STAYS ON THE GATE'S OWN CAMERA. See `WatchReach` on the
		// look asset: there is no pawn to give it back to, and giving it back
		// anyway put a template mannequin on a blue disc at the world origin.
		(void)WasWatching;
	}
	if (Theme)
	{
		// The theme does not stop, it goes. Four seconds is about the length
		// of the blend plus the moment after it.
		Theme->FadeOut(4.f, 0.f);
		Theme = nullptr;
	}
	if (Glass)
	{
		// The world comes into focus as the card leaves. Taking the component
		// away outright is a hard cut back to sharp; fading its weight is the
		// same gesture as the theme's.
		Glass->DestroyComponent();
		Glass = nullptr;
	}
	// The camera is NOT destroyed: it stops going round and starts following.
	// See Tick.
}
