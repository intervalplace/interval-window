#include "IntervalDoor.h"
#include "IntervalGate.h"
#include "EngineUtils.h"

#include "IntervalBridgeSubsystem.h"
#include "Blueprint/WidgetTree.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalDoor, Log, All);

// NAMED, NOT ANONYMOUS. Unity builds paste several .cpp files into one
// translation unit, and two anonymous namespaces in one unit are the SAME
// namespace: this file and IntervalGate.cpp both call a colour Ink and a
// colour Quiet, and the plugin stopped compiling the moment the two landed
// in the same blob. A name each, and `using` so no use site changes.
namespace DoorPalette
{
	const FLinearColor Ink(0.92f, 0.90f, 0.82f, 1.f);
	const FLinearColor Quiet(0.68f, 0.66f, 0.60f, 1.f);
	const FLinearColor Warn(0.92f, 0.56f, 0.44f, 1.f);
}
using namespace DoorPalette;

UTextBlock* UIntervalDoorWidget::AddRow(UVerticalBox* Box, const FLinearColor& Colour, int32 Size)
{
	UTextBlock* Row = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	Row->SetColorAndOpacity(FSlateColor(Colour));
	FSlateFontInfo Font = Row->GetFont();
	Font.Size = Size;
	Row->SetFont(Font);
	if (UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Row))
	{
		Slot->SetPadding(FMargin(0.f, 1.f));
	}
	return Row;
}

TSharedRef<SWidget> UIntervalDoorWidget::RebuildWidget()
{
	// Built here rather than in an asset: a door that reports the rules should
	// live beside them, and a widget tree constructed in code cannot drift
	// away from the fields it is supposed to show.
	if (!WidgetTree->RootWidget)
	{
		UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("DoorFrame"));
		Frame->SetBrushColor(FLinearColor(0.02f, 0.025f, 0.03f, 0.62f));
		Frame->SetPadding(FMargin(14.f, 10.f));
		Frame->SetHorizontalAlignment(HAlign_Left);
		Frame->SetVerticalAlignment(VAlign_Top);

		UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("DoorBox"));
		Frame->SetContent(Box);

		WorldRow     = AddRow(Box, Ink,   15);
		CitizenRow   = AddRow(Box, Quiet, 12);
		IntervalRow  = AddRow(Box, Ink,   13);
		AgreementRow = AddRow(Box, Quiet, 12);
		StandingRow  = AddRow(Box, Ink,   13);
		KeyRow       = AddRow(Box, Quiet, 11);

		WidgetTree->RootWidget = Frame;
	}
	return Super::RebuildWidget();
}

void UIntervalDoorWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
	Super::NativeTick(Geometry, DeltaSeconds);
	if (!Bridge || !WorldRow)
	{
		return;
	}

	const FIntervalFrame& Frame = Bridge->GetFrame();

	if (!Bridge->IsConnected())
	{
		WorldRow->SetText(FText::FromString(TEXT("no bridge")));
		WorldRow->SetColorAndOpacity(FSlateColor(Warn));
		CitizenRow->SetText(FText::FromString(TEXT("start unreal-bridge.mjs and this window fills in")));
		IntervalRow->SetText(FText::GetEmpty());
		AgreementRow->SetText(FText::GetEmpty());
		StandingRow->SetText(FText::GetEmpty());
		KeyRow->SetText(FText::GetEmpty());
		return;
	}
	WorldRow->SetColorAndOpacity(FSlateColor(Ink));

	const FString WorldId = Bridge->GetWorldId();
	int32 W = 0, H = 0;
	Bridge->GetWorldSize(W, H);
	WorldRow->SetText(FText::FromString(FString::Printf(TEXT("world %s…   %d × %d"),
		*WorldId.Left(12), W, H)));

	CitizenRow->SetText(FText::FromString(FString::Printf(TEXT("citizen %s…"),
		*Bridge->GetPlayerId().Left(16))));

	IntervalRow->SetText(FText::FromString(FString::Printf(TEXT("interval %lld"), Frame.Tick)));

	// FINALIZED IS THE NUMBER THAT MATTERS. The interval climbs whether or not
	// anyone agrees; the finalized one only moves when the witnesses do.
	const int64 Behind = Frame.Tick - Frame.FinalizedTick;
	AgreementRow->SetText(FText::FromString(FString::Printf(
		TEXT("finalized %lld  (%lld behind)   witnesses %d of %d"),
		Frame.FinalizedTick, Behind, Frame.Witnesses, Frame.Quorum)));
	AgreementRow->SetColorAndOpacity(FSlateColor(Behind > 5 ? Warn : Quiet));

	// Where the citizen is standing, or how far through a birth they are.
	if (Frame.bHasMe)
	{
		StandingRow->SetText(FText::FromString(FString::Printf(TEXT("standing at %d, %d"),
			Frame.Me.X, Frame.Me.Y)));
		StandingRow->SetColorAndOpacity(FSlateColor(Ink));
	}
	else if (Frame.BirthState == TEXT("waiting"))
	{
		StandingRow->SetText(FText::FromString(FString::Printf(
			TEXT("waiting to be born: %d of %d"), Frame.BirthWaited, Frame.BirthRipeAt)));
		StandingRow->SetColorAndOpacity(FSlateColor(Quiet));
	}
	else if (Frame.BirthState == TEXT("ripe"))
	{
		StandingRow->SetText(FText::FromString(TEXT("the wait is up, crossing")));
		StandingRow->SetColorAndOpacity(FSlateColor(Ink));
	}
	else
	{
		StandingRow->SetText(FText::FromString(TEXT("not in this world: nobody has knocked")));
		StandingRow->SetColorAndOpacity(FSlateColor(Warn));
	}

	// The path, never the bytes. See the header.
	KeyRow->SetText(FText::FromString(FString::Printf(
		TEXT("this citizen is the file %s, held by the bridge, never by this window"),
		*Bridge->GetKeyFile())));
}

// ----------------------------------------------------------------------------

AIntervalDoor::AIntervalDoor()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AIntervalDoor::BeginPlay()
{
	Super::BeginPlay();
	if (!bShowDoor)
	{
		return;
	}

	// ---- AND NOT IF THE GATE IS HERE ----
	//
	// THIS DOOR WAS SUPERSEDED AND NOBODY TOLD IT. AIntervalGate is the
	// window's door now -- the title card, the theme, the camera over the
	// country -- and this one went on drawing its own two rows in the corner
	// of it: "standing at 467, 265" over the world's name, in a different
	// hand, for weeks. Deleting the actor would need a level edit, which this
	// project cannot make stick; standing down when the newer one is present
	// is the same answer and survives a rebuild.
	//
	// It is not deleted because it is still the right door for a window with
	// no gate -- one that only watches, or one being photographed in Simulate
	// where the gate takes itself down.
	{
		TActorIterator<AIntervalGate> Newer(GetWorld());
		if (Newer)
		{
			UE_LOG(LogIntervalDoor, Log,
				TEXT("standing down: AIntervalGate is the door in this level"));
			return;
		}
	}

	UGameInstance* GameInstance = GetGameInstance();
	UIntervalBridgeSubsystem* Found = GameInstance ? GameInstance->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	if (!Found)
	{
		UE_LOG(LogIntervalDoor, Error, TEXT("no bridge subsystem: is the plugin enabled?"));
		return;
	}

	Widget = CreateWidget<UIntervalDoorWidget>(GetWorld(), UIntervalDoorWidget::StaticClass());
	if (!Widget)
	{
		UE_LOG(LogIntervalDoor, Error, TEXT("could not build the door"));
		return;
	}
	Widget->Bridge = Found;
	Widget->AddToViewport(10);
	UE_LOG(LogIntervalDoor, Log, TEXT("door open"));
}

void AIntervalDoor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Widget)
	{
		Widget->RemoveFromParent();
		Widget = nullptr;
	}
	Super::EndPlay(EndPlayReason);
}
