i am researching ballistic shockwaves with respect to a gunshot. the metaphor that has been used to explain and visualise the nature of this sound wave is of a boat sailing through a river with the waves pushed outwards (perpendicular) from the front of the boat until the energy of that wave subsides.

questions:
1. once the bullet has hit a target, is it possible that the sonic shockwave move forward for some distances beyond the point of impact?
2. how can the radius of the shockwave cone be calculated such that a catchment can be modeled of a microphone within able to record the event and the very close microphone outside the catchment unable to record the event?


https://share.google/aimode/YuqDKJhsiJsFhBKsl


To understand ballistic shockwaves, it is helpful to refine the boat metaphor: while the boat creates a wake that follows its path, the "sonic boom" of a bullet is a continuous conical pressure wave trailing the projectile as long as it remains supersonic. [1] 
1. Shockwave Propagation Post-Impact
Yes, the sonic shockwave continues to move forward after the bullet hits a target. [1, 2] 

* Detachment and Continuation: The shockwave is not "attached" to the bullet like a physical object; it is a front of compressed air molecules. When the bullet stops abruptly upon impact, the wave that was already in motion continues to propagate forward at the speed of sound.
* Dissipation: Without the bullet to continuously "push" and reinforce the wave, it stops being a "shock" (a supersonic pressure jump) and transitions into a standard acoustic wave. It will travel a certain distance before its energy subsides and it becomes inaudible.
* Impact Sound: At the moment of impact, a new, distinct sound is often created (the "thud" or "crack" of the hit), which radiates spherically from the target. [1, 2, 3, 4, 5] 

2. Calculating the Shockwave Catchment
The "catchment" area where a microphone can record the shockwave is defined by the Mach Cone. To model whether a microphone is inside or outside this cone, you need to calculate the Mach Angle ($\alpha$).
The Formula
The radius of the cone at any point depends on the distance from the bullet's path and the bullet's velocity. The angle of the cone is calculated as:
$$\sin(\alpha) = \frac{1}{M} = \frac{c}{v}$$ 
Where: [6] 

* $\alpha$ is the Mach Angle (half the total angle of the cone tip).
* $c$ is the speed of sound (approx. $343\text{ m/s}$ at $20^\circ\text{C}$).
* $v$ is the velocity of the bullet.
* $M$ is the Mach Number ($v / c$). [6, 7, 8] 

Modeling the Catchment
To determine if a microphone at a specific coordinate $(x, y)$ can "hear" the shockwave:

   1. Calculate the Mach Angle: A faster bullet creates a narrower, "sharper" cone. For a bullet traveling at $800\text{ m/s}$ (Mach 2.33), the angle $\alpha$ is approximately $25.4^\circ$.
   2. Define the Cone Boundary: At a distance $D$ along the bullet's flight path, the radius $R$ of the shockwave cone is:
   $$R = D \times \tan(\alpha)$$ 
   3. The Detection Zone: A microphone is "inside" the catchment if its perpendicular distance from the bullet's trajectory is less than the radius of the cone at that moment in time. [9, 10] 

Would you like to calculate the specific time delay between the shockwave and the muzzle blast for a particular firearm and microphone setup?

[1] [https://www.youtube.com](https://www.youtube.com/shorts/D7HlhhlNLbY)
[2] [https://journals.sagepub.com](https://journals.sagepub.com/doi/full/10.1258/msl.2011.010117)
[3] [https://www.americanscientist.org](https://www.americanscientist.org/article/high-speed-imaging-of-shock-waves-explosions-and-gunshots)
[4] [https://www.reddit.com](https://www.reddit.com/r/askscience/comments/4i4u8o/when_i_hear_a_sonic_boom_am_i_hearing_all_the/)
[5] [https://www.researchgate.net](https://www.researchgate.net/publication/221709514_Using_sound_of_target_impact_for_acoustic_reconstructions_of_shooting_events)
[6] [https://courses.lumenlearning.com](https://courses.lumenlearning.com/suny-osuniversityphysics/chapter/17-8-shock-waves/)
[7] [https://ffden-2.phys.uaf.edu](http://ffden-2.phys.uaf.edu/webproj/211_fall_2016/Andrew_Bray/Andrew_Bray/physics.html#:~:text=When%20an%20object%20moves%20through%20the%20air,the%20speed%20of%20sound%28c%29%20or%20Mach%201.)
[8] [https://www.sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S0003682X10001283#:~:text=The%20angle%20of%20the%20shock%20wave%20front,v%20is%20the%20speed%20of%20the%20bullet.)
[9] [https://www.researchgate.net](https://www.researchgate.net/figure/Shock-wave-geometry-for-a-supersonic-Mach-3-projectile-and-a-slower-supersonic-Mach-105_fig1_228900815)
[10] [https://link.springer.com](https://link.springer.com/chapter/10.1007/978-3-319-99453-6_9#:~:text=A%20projectile%20with%20speed%20just%20barely%20above,%CE%B8%20M%20%E2%86%92%2016.6%20%C2%B0%29.%20See%20Fig.)



> Detachment and Continuation: The shockwave is not "attached" to the bullet like a physical object; it is a front of compressed air molecules. When the bullet stops abruptly upon impact, the wave that was already in motion continues to propagate forward at the speed of sound.

https://share.google/aimode/upbZPg4EDnAs6zUOw

prior to the "Detachment and Continuation" the shockwave could be detected visually in waveform with it's "N" signature and in a spectrogram with the registered frequencies. however, upon "Detachment and Continuation" its velocity changes to the speed of sound, but what happens to the waveform and spectrogram signatures? 

When the bullet impacts a target, the "engine" driving the shockwave disappears. The transition from a driven shockwave to a free-travelling acoustic wave changes the signal significantly:
1. The Waveform (The "N-wave" degradation)
Prior to impact, the "N" shape is maintained by the extreme pressure gradient at the bullet's tip (compression) and tail (rarefaction).

* Rounding of Edges: Once detached, the nearly instantaneous pressure jumps (the vertical lines of the "N") begin to "smear." The air's natural viscosity and thermal conductivity act as a low-pass filter.
* Loss of Amplitude: Without the bullet's kinetic energy to reinforce it, the peak pressure drops rapidly ($1/r$ relationship for distance).
* Transition to Sine: Eventually, the sharp N-wave stretches and rounds out until it resembles a standard, decaying bipolar pulse or a dampened sine wave.

2. The Spectrogram (Frequency shift)
The spectrogram of a supersonic shockwave is characterized by a very wide "white noise" burst because the instantaneous pressure jump contains energy across almost all frequencies.

* High-Frequency Roll-off: The "crack" sound loses its crispness. In a spectrogram, you would see the energy in the upper kilohertz (10kHz–20kHz+) vanish first.
* Frequency Lowering: As the wave "stretches" (the N-wave gets longer in duration as it travels), the dominant frequency energy shifts downward into the lower-mid range.
* Duration Smearing: The signal becomes less "tight" in time. What was a microsecond-scale event spreads out into a millisecond-scale acoustic event.

3. Velocity and Phase
The most critical change is the propagation geometry.

* Before Impact: The wave moves at the "Mach speed" relative to the ground, but its wavefront is angled.
* After Impact: The detached front immediately begins to behave as a spherical acoustic wave originating from the last point of supersonic flight. It slows down to the local speed of sound ($c$) and begins to follow standard Huygens’ Principle expansion.

In summary: The "crack" of the supersonic bullet turns into a "pop" or "thud" as it detaches and travels forward, eventually becoming indistinguishable from the ambient noise.
Should we look into how atmospheric humidity or temperature might accelerate this decay in your model?


