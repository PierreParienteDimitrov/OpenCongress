"""
Generate hemicycle seats for visualization.

Usage:
    python manage.py generate_seats
"""

import math

from django.core.management.base import BaseCommand

from apps.congress.models import Member, Seat


class Command(BaseCommand):
    help = "Generate hemicycle seats for House and Senate visualization"

    def handle(self, *args, **options):
        self.stdout.write("Generating seats...")

        # Clear existing seats
        Seat.objects.all().delete()

        # Generate House seats (435)
        house_seats = self._generate_house_seats()
        self.stdout.write(f"Generated {len(house_seats)} House seats")

        # Generate Senate seats (100)
        senate_seats = self._generate_senate_seats()
        self.stdout.write(f"Generated {len(senate_seats)} Senate seats")

        # Assign members to seats
        self._assign_members_to_seats()

        total = Seat.objects.count()
        assigned = Seat.objects.exclude(member=None).count()
        self.stdout.write(
            self.style.SUCCESS(f"Done! {total} seats created, {assigned} assigned to members")
        )

    def _generate_house_seats(self) -> list:
        """Generate 435 House seats in hemicycle layout."""
        seats = []

        # Hemicycle configuration
        # Total seats per row increases as you go back
        rows_config = [
            35,   # Row 1 (front, closest to center)
            42,
            49,
            55,
            60,
            65,
            69,
            60,   # Row 8
        ]

        # We need 435 seats total, adjust last row
        current_total = sum(rows_config)
        if current_total < 435:
            rows_config.append(435 - current_total)

        seat_num = 0
        for row_idx, seats_in_row in enumerate(rows_config):
            row = row_idx + 1

            # Calculate SVG coordinates for hemicycle
            # Hemicycle spans from 0 to 180 degrees
            radius = 150 + (row * 30)  # Radius increases per row
            center_x = 400
            center_y = 350

            for pos in range(seats_in_row):
                seat_num += 1
                if seat_num > 435:
                    break

                # Calculate angle (spread seats across 180 degrees)
                angle_deg = 180 * (pos + 0.5) / seats_in_row
                angle_rad = math.radians(angle_deg)

                # SVG coordinates
                svg_x = center_x - radius * math.cos(angle_rad)
                svg_y = center_y - radius * math.sin(angle_rad)

                # Determine section based on position (left = Dem, right = Rep)
                if pos < seats_in_row * 0.48:
                    section = "democrat"
                elif pos > seats_in_row * 0.52:
                    section = "republican"
                else:
                    section = "independent"

                seat_id = f"house-{row}-{pos + 1}"

                seat = Seat.objects.create(
                    seat_id=seat_id,
                    chamber="house",
                    section=section,
                    row=row,
                    position=pos + 1,
                    svg_x=round(svg_x, 2),
                    svg_y=round(svg_y, 2),
                )
                seats.append(seat)

        return seats

    def _generate_senate_seats(self) -> list:
        """Generate 100 Senate seats in hemicycle layout."""
        seats = []

        # Senate has fewer rows, wider spacing
        rows_config = [
            18,  # Row 1
            22,
            26,
            34,  # Row 4 (back row)
        ]

        seat_num = 0
        for row_idx, seats_in_row in enumerate(rows_config):
            row = row_idx + 1

            radius = 120 + (row * 35)
            center_x = 400
            center_y = 300

            for pos in range(seats_in_row):
                seat_num += 1
                if seat_num > 100:
                    break

                angle_deg = 180 * (pos + 0.5) / seats_in_row
                angle_rad = math.radians(angle_deg)

                svg_x = center_x - radius * math.cos(angle_rad)
                svg_y = center_y - radius * math.sin(angle_rad)

                if pos < seats_in_row * 0.48:
                    section = "democrat"
                elif pos > seats_in_row * 0.52:
                    section = "republican"
                else:
                    section = "independent"

                seat_id = f"senate-{row}-{pos + 1}"

                seat = Seat.objects.create(
                    seat_id=seat_id,
                    chamber="senate",
                    section=section,
                    row=row,
                    position=pos + 1,
                    svg_x=round(svg_x, 2),
                    svg_y=round(svg_y, 2),
                )
                seats.append(seat)

        return seats

    def _assign_members_to_seats(self):
        """Assign members to seats based on party and seniority."""
        for chamber in ["house", "senate"]:
            members = Member.objects.filter(
                chamber=chamber, is_active=True
            ).order_by("party", "-seniority_date", "last_name")

            # Get seats by section
            dem_seats = list(
                Seat.objects.filter(chamber=chamber, section="democrat").order_by(
                    "row", "position"
                )
            )
            rep_seats = list(
                Seat.objects.filter(chamber=chamber, section="republican").order_by(
                    "row", "-position"
                )
            )
            ind_seats = list(
                Seat.objects.filter(chamber=chamber, section="independent").order_by(
                    "row", "position"
                )
            )

            dem_idx = 0
            rep_idx = 0
            ind_idx = 0

            for member in members:
                seat = None

                if member.party == "D" and dem_idx < len(dem_seats):
                    seat = dem_seats[dem_idx]
                    dem_idx += 1
                elif member.party == "R" and rep_idx < len(rep_seats):
                    seat = rep_seats[rep_idx]
                    rep_idx += 1
                elif ind_idx < len(ind_seats):
                    seat = ind_seats[ind_idx]
                    ind_idx += 1
                # Fallback: use opposite party seats if needed
                elif member.party == "D" and rep_idx < len(rep_seats):
                    seat = rep_seats[rep_idx]
                    rep_idx += 1
                elif member.party == "R" and dem_idx < len(dem_seats):
                    seat = dem_seats[dem_idx]
                    dem_idx += 1

                if seat:
                    seat.member = member
                    seat.save()
