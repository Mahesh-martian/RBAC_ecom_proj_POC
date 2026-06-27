import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import Autoplay from "embla-carousel-autoplay";
import Image from "next/image";
import { H2, H3 } from "../shared/CustomTypography";
import CustomButton from "../shared/CustomButton";
import { MoveRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { carouselItems } from "@/constants";
import { cn } from "@/lib/utils";
import imgOne from "../../../public/images/hero1.png";
import imgTwo from "../../../public/images/hero2.png";
import imgThree from "../../../public/images/hero3.png";

const data = [
  {
    heading: "Home Interior",
    img: imgOne,
    title: "Wood & Cloth Sofa",
    desc: "A modern, comfortable sofa with plush cushions, durable fabric, and a sleek design, perfect for any space.",
  },
  {
    heading: "Bike Accessories",
    img: imgTwo,
    title: "Reliable and Stylish Safety Helmet",
    desc: "A sturdy, lightweight helmet with excellent ventilation, a sleek design, and reliable protection for safe rides.",
  },
  {
    heading: "Clothings",
    img: imgThree,
    title: "Comfortable and Durable Running Shoes",
    desc: "Lightweight, breathable shoes with superior cushioning, durable sole, and sleek design for ultimate comfort and performance.",
  },
];

const HomeCarousel = () => {
  const router = useRouter();
  const goToShop = () => {
    router.push("/shop");
  };

  const bgColors = ["#ECFDFF", "#fffcec", "#ecfeff", "#edffec", "#d7ebef"];

  const getRandomHexColor = () => {
    const randomIndex = Math.floor(Math.random() * bgColors.length); // Random index
    return bgColors[randomIndex]; // Return the hex color
  };

  return (
    <Carousel
      plugins={[Autoplay({ delay: 8000 })]}
      opts={{
        align: "start",
        loop: true,
      }}
    >
      <CarouselContent>
        {data.map((item, i) => (
          <CarouselItem key={i}>
            <div
              style={{ backgroundColor: getRandomHexColor() }}
              className={cn(
                "rounded-lg flex p-4 justify-between items-center h-[40vh] lg:h-[60vh]",
              )}
            >
              <div className="grid grid-cols-2 gap-8">
                <div className="col-span-1 flex flex-col justify-center gap-4">
                  <H3 className="text-primary dark:text-primary lg:text-2xl">
                    {item.heading}
                  </H3>
                  <div className="pb-3">
                    <H2 className="lg:text-6xl mb-4">{item.title}</H2>
                    <p className="font-medium my-4 xl:max-w-[550px]">
                      {item.desc}
                    </p>
                  </div>

                  <div>
                    <CustomButton
                      icon={<MoveRight />}
                      className="lg:py-6 inline-flex"
                      iconPosition="right"
                      onClick={goToShop}
                    >
                      Shop Now
                    </CustomButton>
                  </div>
                </div>
                <div className="col-span-1 flex items-center justify-center">
                  <Image
                    src={item.img}
                    height={400}
                    width={400}
                    alt={item.title}
                    className="object-cover w-full h-full max-w-[500px] rounded-lg lg:p-10"
                  />
                </div>
              </div>
            </div>
          </CarouselItem>
        ))}
      </CarouselContent>
    </Carousel>
  );
};

export default HomeCarousel;
