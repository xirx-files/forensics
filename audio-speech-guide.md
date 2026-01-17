https://www.google.com/search?q=what+should+i+expect+if+i+run+an+high+pass+filter+in+audacity+of+a+recording+of+a+person+saying+the+word+%22violence%22+%26+%22great%22.+do+either+of+these+words+have+critical+features+in+their+signature+which+make+then+detectable+under+varying+conditions+of+background+noise&sca_esv=4ba3af865432350d&hl=en&source=hp&ei=P_pqaZXzJ-bsseMP8-m98Qw&iflsig=AFdpzrgAAAAAaWsIT8gc3WBu_ck0LhBw3BiVt6j_U6as&aep=22&udm=50&ved=0ahUKEwjVjvfHyZGSAxVmdmwGHfN0L84QteYPCBk&oq=&gs_lp=Egdnd3Mtd2l6IgBIAFAAWABwAHgAkAEAmAEAoAEAqgEAuAEByAEAmAIAoAIAmAMAkgcAoAcAsgcAuAcAwgcAyAcAgAgA&sclient=gws-wiz&mstk=AUtExfCLeAAeyqaVfJjPl4crMaA_Q6DNT0fg2nAuBTb_phsmh1EqlTawOWq_Y--fcMkVvUpXB6xo6NS5Kbt5_YdNW6hCymXMtaBMIB4eRT35bX7JgSLHEnp72YRFfZJziWpIaNf0vgYUesiTle4_EU9SP1ggJcqN7w2lfGAr9wiD6Ut_NAr5QE2EPlpha2cZ-LdsqstgdvTYbp3oRMwlK3JS7ksWQ3ley1jhJJT6Gy54xbYU9ST6GlzPlvaBUQ&csuir=1


    what should i expect if i run an high pass filter in audacity of a recording of a person saying the word "violence" & "great". do either of these words have critical features in their signature which make then detectable under varying conditions of background noise


Running a high-pass filter (HPF) in Audacity on a person saying "violence" and "great" will yield distinct auditory results based on the phonemes in each word. The filter allows frequencies above a set cutoff to pass while attenuating lower frequencies. 
Expected Auditory Effects
Word: "Violence"
The "v" (voiced fricative): As a voiced sound, it has low-frequency energy (the "voice bar"). A high-pass filter set above ~300 Hz will remove this warmth, making the "v" sound thinner and more like an "f".
The vowels ("i-o-e"): HPFs will strip away the first formants (typically below 1000 Hz), which provide vocal body and identity. The word will sound "tinny" or like it is coming through a small telephone speaker.
The "nce" (sibilant fricative): This part contains high-frequency energy (often 4,000–8,000 Hz). It will remain largely unaffected and may even sound more prominent once the competing low frequencies are removed.
Word: "Great"
The "gr" (plosive + liquid): The "g" is a low-frequency burst. A high-pass filter will weaken this "thud," making the start of the word sound sharp but less authoritative.
The "t" (stop/plosive): The final "t" is a high-frequency burst. Like the sibilance in "violence," it will remain clear and sharp even with aggressive high-pass filtering. 
Critical Detectability Features
Both words contain "fingerprint" features that remain detectable under varying background noise:
Sibilance (The "s" in Violence): Fricatives like /s/ have high-energy signatures in the 4–10 kHz range. Because most ambient noise (engines, rumble, fans) is low-frequency, the "s" sound often cuts through noise even when the rest of the word is masked.
Plosive Bursts (The "g" and "t" in Great): The rapid release of air in "t" creates a sharp transient spike on a spectrogram. These sudden changes in energy are often detectable against steady-state background noise (like white noise or wind) because they don't follow the same rhythmic pattern as the noise.
Vowel Transitions (Diphthongs): The word "violence" has complex vowel transitions. While the low-frequency "warmth" is lost with filtering, the higher-frequency formants (F2 and F3) still move in a specific pattern that a listener's brain can often use to reconstruct the word, even in noisy environments. 
In Audacity, you can find this under Effect > EQ and Filters > High-Pass Filter. A typical setting to clean up speech without losing intelligibility is a cutoff between 80 Hz and 150 Hz with a 12 dB or 24 dB rolloff. 
This information breaks down the auditory effects of applying Audacity's high-pass filter to specific words and identifies critical phonetic features that aid in their detection under noisy conditions.